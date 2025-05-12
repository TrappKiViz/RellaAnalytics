import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import { 
    DashboardOutlined, 
    SettingOutlined, 
    DatabaseOutlined, 
    UserOutlined,
    LogoutOutlined,
    AreaChartOutlined, // Example for Customer Insights
    DollarCircleOutlined // Example for Profitability
} from '@ant-design/icons';
import { useAuth } from '../../context/AuthContext'; // Adjust path as needed

const { Sider } = Layout;

function Sidebar({ collapsed }) {
    const location = useLocation();
    const { logout } = useAuth();

    // Determine selected keys based on current path
    // Basic matching, could be more sophisticated if needed
    const selectedKeys = [location.pathname]; 

    return (
        <Sider trigger={null} collapsible collapsed={collapsed} width={200}>
            <div className="logo" style={{ height: '32px', margin: '16px', background: 'rgba(255, 255, 255, 0.3)' }} />
            <Menu theme="dark" mode="inline" selectedKeys={selectedKeys}>
                <Menu.Item key="/" icon={<DashboardOutlined />}>
                    <Link to="/">Dashboard</Link>
                </Menu.Item>
                <Menu.Item key="/profitability" icon={<DollarCircleOutlined />}>
                    <Link to="/profitability">Profitability Analytics</Link>
                </Menu.Item>
                <Menu.Item key="/customer-insights" icon={<AreaChartOutlined />}>
                    <Link to="/customer-insights">Customer Insights</Link>
                </Menu.Item>
                <Menu.Item key="/data" icon={<DatabaseOutlined />}>
                    <Link to="/data">Data Management</Link>
                </Menu.Item>
                <Menu.Item key="/settings" icon={<SettingOutlined />}>
                    <Link to="/settings">Settings</Link>
                </Menu.Item>
                <Menu.Divider /> 
                <Menu.Item key="logout" icon={<LogoutOutlined />} onClick={logout}>
                    Logout
                </Menu.Item>
            </Menu>
        </Sider>
    );
}

export default Sidebar; 