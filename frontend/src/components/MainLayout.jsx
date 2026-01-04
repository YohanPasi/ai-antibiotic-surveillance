import React, { useState } from 'react';
import Dashboard from './Dashboard';
import WardDetail from './WardDetail';
import AuditLog from './AuditLog';
import MRSAPage from './MRSAPage';
import MasterDataManager from './MasterDataManager';
import ASTEntryForm from './ASTEntryForm';
import Sidebar from './Sidebar';
import MRSAPerformanceDashboard from './MRSAPerformanceDashboard';
import Header from './Header';
import { useAuth } from '../context/AuthContext';

function MainLayout() {
    const [activeView, setActiveView] = useState('dashboard');
    const [selectedWard, setSelectedWard] = useState(null);
    const { logout } = useAuth(); // Sidebar handles logout button

    // Helper to handle navigation from Sidebar
    // Sidebar passes IDs: 'dashboard', 'ward_detail', 'audit_log'
    // MainLayout maps them to render logic.
    const handleViewChange = (viewId) => {
        if (viewId === 'ward_detail' && !selectedWard) {
            // Should probably go to a ward list or just force ICU default?
            // For now, let's just create a view for "Select Ward" or default to dashboard
            setSelectedWard(null); // Reset selection to force selection screen if we had one
        }
        setActiveView(viewId);
    };

    const renderContent = () => {
        switch (activeView) {
            case 'dashboard':
                return (
                    <>
                        <Dashboard
                            setActiveView={setActiveView}
                            setSelectedWard={setSelectedWard}
                            engineVersion="Hybrid_LSTM_v1"
                        />
                        {/* Audit Log is part of Dashboard view or separate? 
                            Original code had <AuditLog /> below dashboard. 
                            If 'audit_log' is a separate page in Sidebar, we should render it separately.
                        */}
                    </>
                );
            case 'ward_detail':
                return (
                    <WardDetail
                        wardId={selectedWard} // Will be null if navigated directly via Sidebar
                        goBack={() => setActiveView('dashboard')}
                    />
                );
            case 'mrsa_prediction':
                return <MRSAPage />;
            case 'master_data':
                return <MasterDataManager />;
            case 'audit_log':
                return <AuditLog />;
            case 'ast_entry':
                // Using ASTEntryForm as a pseudo-page (modal usually, but we force open)
                return (
                    <div className="h-full flex items-center justify-center p-10">
                        {/* We pass isOpen=true. 
                             Since it has "fixed inset-0", it will overlay. 
                             Ideally we would refactor it to be a page, but for now we just render it. 
                             Wait, if we render it here, the specific 'onClose' behavior needs to be handled.
                          */}
                        <ASTEntryForm
                            isOpen={true}
                            onClose={() => setActiveView('dashboard')}
                            onEntrySaved={() => setActiveView('dashboard')}
                        />
                        {/* Placeholder background since form is fixed position overlay */}
                        <div className="text-slate-500">Opening Lab Entry Interface...</div>
                    </div>
                );
            case 'analytics':
                return <MRSAPerformanceDashboard />;
            default:
                return <div className="text-white">View Not Found</div>;
        }
    };

    return (
        <div className="flex h-screen bg-white dark:bg-gray-900 text-slate-900 dark:text-gray-100 font-sans overflow-hidden transition-colors duration-300">
            {/* Sidebar (Fixed Left) */}
            <Sidebar
                activeView={activeView}
                setActiveView={handleViewChange}
                logout={logout}
            />

            {/* Main Content Area (Flex Grow) */}
            <div className="flex-1 flex flex-col min-w-0">
                <Header />

                {/* Scrollable Content */}
                <main className="flex-1 overflow-y-auto p-6 scrollbar-thin scrollbar-thumb-gray-800 scrollbar-track-transparent">
                    <div className="max-w-7xl mx-auto">
                        {renderContent()}
                    </div>
                </main>

                <footer className="py-4 px-6 border-t border-gray-200 dark:border-gray-800 text-center text-xs text-gray-500 dark:text-gray-600 bg-gray-50 dark:bg-gray-900 transition-colors">
                    <p>© 2025 Antigravity Surveillance Project | Confidential Clinical Data</p>
                </footer>
            </div>
        </div>
    );
}

export default MainLayout;
