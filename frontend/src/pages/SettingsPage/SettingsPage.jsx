import React, { useState } from 'react';
import './SettingsPage.css'; // Add CSS file

function SettingsPage() {
    // Example state for settings - load actual values later
    const [crmType, setCrmType] = useState('none'); // e.g., 'salesforce', 'hubspot', 'none'
    const [crmApiKey, setCrmApiKey] = useState('');
    const [crmUsername, setCrmUsername] = useState(''); // Add CRM username state
    const [crmPassword, setCrmPassword] = useState(''); // Add CRM password state
    const [syncEnabled, setSyncEnabled] = useState(false);

    // Placeholder user info - fetch real info later
    const [userName, setUserName] = useState('Demo User');
    const [userEmail, setUserEmail] = useState('demo@example.com');
    const [userOrg, setUserOrg] = useState('Rella Analytics Inc.');

    const handleSaveSettings = (e) => {
        e.preventDefault();
        // TODO: Implement API call to save settings
        // Example: await saveCrmSettings({ type: crmType, apiKey: crmApiKey, enabled: syncEnabled, username: crmUsername, password: crmPassword });
        console.log('Placeholder: Settings save action triggered for CRM Type:', crmType);
    };

     const handleChangePassword = () => {
        // TODO: Implement change password flow (e.g., modal, separate page)
        alert("Change password functionality not implemented yet.");
    };

    return (
        <div className="settings-page">
            <h1>Settings</h1>

            <section className="settings-section">
                <h2>User Account</h2>
                <div className="form-group">
                     <label htmlFor="user-name">Name:</label>
                     <input type="text" id="user-name" value={userName} readOnly />
                </div>
                 <div className="form-group">
                     <label htmlFor="user-email">Email:</label>
                     <input type="email" id="user-email" value={userEmail} readOnly />
                </div>
                 <div className="form-group">
                     <label htmlFor="user-org">Organization:</label>
                     <input type="text" id="user-org" value={userOrg} readOnly />
                </div>
                <button onClick={handleChangePassword} className="button-secondary">Change Password</button>
            </section>

            <section className="settings-section">
                <h2>CRM Integration</h2>
                <p>Configure connection to your Customer Relationship Management system.</p>
                <form onSubmit={handleSaveSettings}> 
                    <div className="form-group">
                        <label htmlFor="crm-type">CRM System:</label>
                        <select
                            id="crm-type"
                            value={crmType}
                            onChange={(e) => setCrmType(e.target.value)}
                        >
                            <option value="none">None</option>
                            <option value="salesforce">Salesforce (Future)</option>
                            <option value="hubspot">HubSpot (Future)</option>
                            {/* Add other CRM options */}
                        </select>
                    </div>
                    {crmType !== 'none' && (
                        <>
                             <div className="form-group">
                                <label htmlFor="crm-username">CRM Username/Email:</label>
                                <input
                                    type="text"
                                    id="crm-username"
                                    value={crmUsername}
                                    onChange={(e) => setCrmUsername(e.target.value)}
                                    placeholder="Enter CRM Login Username/Email"
                                />
                            </div>
                             <div className="form-group">
                                <label htmlFor="crm-password">CRM Password/Token:</label>
                                <input
                                    type="password" 
                                    id="crm-password"
                                    value={crmPassword}
                                    onChange={(e) => setCrmPassword(e.target.value)}
                                    placeholder="Enter CRM Password or App Token"
                                />
                            </div>
                            <div className="form-group">
                                <label htmlFor="crm-api-key">API Key (Optional/Alternative):</label>
                                <input
                                    type="password" // Use password type for sensitive keys
                                    id="crm-api-key"
                                    value={crmApiKey}
                                    onChange={(e) => setCrmApiKey(e.target.value)}
                                    placeholder="Enter CRM API Key (if applicable)"
                                />
                            </div>
                            <div className="form-group checkbox-group">
                                <input
                                    type="checkbox"
                                    id="crm-sync"
                                    checked={syncEnabled}
                                    onChange={(e) => setSyncEnabled(e.target.checked)}
                                />
                                <label htmlFor="crm-sync">Enable Data Sync (Future)</label>
                            </div>
                        </>
                    )}
                    {/* Disable button more reliably based on CRM type */}
                    <button type="submit" disabled={crmType === 'none'}>Save CRM Settings</button> 
                </form>
            </section>

             {/* Add more settings sections here later */}

        </div>
    );
}

export default SettingsPage;
