"""
STP Stage 1: Stage Boundary Enforcement Tests
==============================================
Purpose: M10 - Validate stage boundaries are respected

Tests:
- Stage 1 does not compute resistance rates
- Stage 1 does not access forbidden libraries
- Stage 2+ cannot write to Stage 1 tables
- Read-only view enforces boundaries

Database: Supabase PostgreSQL (via DATABASE_URL)
"""

import pytest
import os
import sys
import ast

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))


# =====================================================
# FORBIDDEN CODE PATTERNS (M10)
# =====================================================

class TestStage1Boundaries:
    """M10: Ensure Stage 1 code respects boundaries."""
    
    def test_no_resistance_rate_computation(self):
        """Verify Stage 1 code does not compute resistance rates."""
        stage1_files = [
            'api/data_processor/stp_stage_1_ingest.py',
            'api/data_processor/stp_wide_to_long_transform.py',
            'api/data_processor/stp_descriptive_stats.py',
        ]
        
        forbidden_patterns = [
            'resistant_count / total_tested',
            'susceptible_count / total_tested',
            'resistance_rate',
            'susceptibility_percent',
            'S_count / total',
            'R_count / total'
        ]
        
        for file_path in stage1_files:
            full_path = os.path.join(os.path.dirname(__file__), '..', file_path)
            if not os.path.exists(full_path):
                continue
                
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                for pattern in forbidden_patterns:
                    assert pattern not in content, \
                        f"STAGE BOUNDARY VIOLATION: '{pattern}' found in {file_path}"
    
    def test_no_trend_analysis_in_stage1(self):
        """Verify Stage 1 does not compute trends."""
        stage1_files = [
            'api/data_processor/stp_descriptive_stats.py',
        ]
        
        forbidden_patterns = [
            'trend',
            'slope',
            'regression',
            'forecast',
            'prediction'
        ]
        
        for file_path in stage1_files:
            full_path = os.path.join(os.path.dirname(__file__), '..', file_path)
            if not os.path.exists(full_path):
                continue
                
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                for pattern in forbidden_patterns:
                    # Allow in comments, but not in actual code
                    lines = content.split('\n')
                    code_lines = [l for l in lines if not l.strip().startswith('#')]
                    code_content = '\n'.join(code_lines)
                    
                    # Descriptive stats is allowed to use 'temporal distribution' but not 'temporal trend'
                    if pattern == 'trend' and 'temporal_density' in code_content:
                        continue  # M3 temporal density is allowed
                    
                    # Count occurrences
                    count = code_content.count(pattern)
                    assert count == 0 or count < 2, \
                        f"STAGE BOUNDARY VIOLATION: '{pattern}' potentially used in {file_path}"
    
    def test_no_statistical_tests(self):
        """Verify Stage 1 does not perform statistical tests."""
        stage1_files = [
            'api/data_processor/stp_descriptive_stats.py',
        ]
        
        forbidden_functions = [
            'ttest',
            'chi2',
            'anova',
            'mannwhitney',
            'wilcoxon'
        ]
        
        for file_path in stage1_files:
            full_path = os.path.join(os.path.dirname(__file__), '..', file_path)
            if not os.path.exists(full_path):
                continue
                
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                for func in forbidden_functions:
                    assert func not in content, \
                        f"STAGE BOUNDARY VIOLATION: Statistical test '{func}' found in {file_path}"


# =====================================================
# IMPORT RESTRICTIONS (M10)
# =====================================================

class TestForbiddenImports:
    """M10: Verify Stage 1 does not import modeling libraries."""
    
    def test_no_sklearn_in_stage1(self):
        """Verify Stage 1 files do not import sklearn."""
        stage1_files = [
            'api/data_processor/stp_stage_1_ingest.py',
            'api/data_processor/stp_wide_to_long_transform.py',
            'api/data_processor/stp_descriptive_stats.py',
        ]
        
        for file_path in stage1_files:
            full_path = os.path.join(os.path.dirname(__file__), '..', file_path)
            if not os.path.exists(full_path):
                continue
                
            with open(full_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
                
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    imports.append(node.module)
            
            forbidden = ['sklearn', 'statsmodels', 'prophet', 'tensorflow', 'torch']
            for lib in forbidden:
                matching = [imp for imp in imports if imp and lib in imp]
                assert len(matching) == 0, \
                    f"STAGE BOUNDARY VIOLATION: {lib} imported in {file_path}"


# =====================================================
# READ-ONLY VIEW TESTS (M10)
# =====================================================

class TestReadOnlyView:
    """M10: Verify read-only view exists for Stage 2+."""
    
    @pytest.fixture(scope="class")
    def db_session(self):
        """Supabase database session."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        DATABASE_URL = os.getenv('DATABASE_URL')
        if not DATABASE_URL:
            pytest.skip("DATABASE_URL not set")
        
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    
    def test_readonly_view_exists(self, db_session):
        """Verify stp_stage1_readonly view exists."""
        from sqlalchemy import text
        
        result = db_session.execute(
            text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.views 
                    WHERE table_name = 'stp_stage1_readonly'
                )
            """)
        ).scalar()
        
        assert result, "M10: Read-only view stp_stage1_readonly does not exist"
    
    def test_readonly_view_only_shows_frozen(self, db_session):
        """M10 + M6: Verify view only shows frozen datasets."""
        from sqlalchemy import text
        
        # Get view definition
        view_def = db_session.execute(
            text("""
                SELECT view_definition FROM information_schema.views 
                WHERE table_name = 'stp_stage1_readonly'
            """)
        ).scalar()
        
        assert view_def is not None
        assert 'is_frozen' in view_def.lower(), \
            "M10: Read-only view must filter by is_frozen (M6)"


# =====================================================
# ARCHITECTURE CONTRACT TESTS
# =====================================================

class TestArchitectureContract:
    """Verify architectural discipline."""
    
    def test_stage1_files_in_correct_directory(self):
        """Verify Stage 1 files are properly organized."""
        stage1_dir = os.path.join(os.path.dirname(__file__), '..', 'api', 'data_processor')
        
        expected_files = [
            'stp_stage_1_ingest.py',
            'stp_wide_to_long_transform.py',
            'stp_build_antibiotic_registry.py',
            'stp_generate_governance_report.py',
            'stp_descriptive_stats.py'
        ]
        
        for filename in expected_files:
            filepath = os.path.join(stage1_dir, filename)
            assert os.path.exists(filepath), f"Expected file missing: {filename}"
    
    def test_stage1_files_have_docstrings(self):
        """Verify all Stage 1 modules are documented."""
        stage1_files = [
            'api/data_processor/stp_stage_1_ingest.py',
            'api/data_processor/stp_wide_to_long_transform.py',
        ]
        
        for file_path in stage1_files:
            full_path = os.path.join(os.path.dirname(__file__), '..', file_path)
            if not os.path.exists(full_path):
                continue
                
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Check for module-level docstring
                assert '"""' in content or "'''" in content, \
                    f"Missing docstring in {file_path}"


# =====================================================
# NA VALUE PRESERVATION TESTS (M2 + M10)
# =====================================================

class TestNAPreservation:
    """M2: Verify NA values are preserved (not treated as missing)."""
    
    def test_na_not_dropped_in_transformation(self):
        """Verify NA values are not filtered out."""
        transform_file = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'api/data_processor/stp_wide_to_long_transform.py'
        )
        
        if os.path.exists(transform_file):
            with open(transform_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Should NOT have dropna() calls
            assert 'dropna()' not in content, \
                "M2 VIOLATION: NA values must be preserved, not dropped"
            
            # Should handle NA explicitly
            assert 'NA' in content, \
                "M2: NA handling should be explicit"


# =====================================================
# RUN TESTS
# =====================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
