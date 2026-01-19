import React, { useState, useEffect } from 'react';
import { Truck, Warehouse, FileText, Package, LayoutDashboard, Users, DollarSign, Settings, ChevronRight, Search, Bell, Menu, X, Send, Paperclip, MessageCircle, CheckCircle, Clock, TrendingUp, BarChart3, Activity } from 'lucide-react';

// Theme colors from 5P Vietnam logo
const theme = {
  primary: '#2563EB',
  primaryDark: '#1E40AF',
  primaryLight: '#3B82F6',
  accent: '#F59E0B',
  accentRed: '#EF4444',
  success: '#10B981',
  warning: '#F59E0B',
  bgLight: '#F8FAFC',
  bgDark: '#1E293B',
  text: '#1E293B',
  textSecondary: '#64748B',
  border: '#E2E8F0',
};

// Service visibility hook simulation
const useServiceVisibility = () => ({
  showTrucking: true,
  showWarehouse: true,
  showCustoms: true,
  showPacking: true,
});

// Sample data
const recentJobs = [
  { id: 'TRK-2601-089', customer: 'DRT1', status: 'pending', type: 'trucking', time: '22:00' },
  { id: 'TRK-2601-088', customer: 'SEVT', status: 'transit', type: 'trucking', time: '14:00' },
  { id: 'PKG-1701-001', customer: 'HSDN', status: 'completed', type: 'packing', time: '10:30' },
  { id: 'CUS-2601-012', customer: 'DS-BN', status: 'pending', type: 'customs', time: '08:00' },
  { id: 'WHS-2601-003', customer: 'DRT2', status: 'active', type: 'warehouse', time: '06:00' },
];

const chatMessages = [
  { role: 'user', content: 'cập nhật (PKG-1701-0001) hoàn thành', time: '18:19:16' },
  { role: 'assistant', content: 'COMPLETE_JOB', intent: 'COMPLETE_JOB', confidence: 95, job: 'PKG-1701-0001', confirmed: true },
];

// Status Badge Component
const StatusBadge = ({ status }) => {
  const styles = {
    pending: { bg: '#FEF3C7', color: '#D97706', label: 'Pending' },
    transit: { bg: '#DBEAFE', color: '#2563EB', label: 'In Transit' },
    completed: { bg: '#D1FAE5', color: '#059669', label: 'Completed' },
    active: { bg: '#E0E7FF', color: '#4F46E5', label: 'Active' },
  };
  const style = styles[status] || styles.pending;
  
  return (
    <span style={{
      padding: '4px 10px',
      borderRadius: '12px',
      fontSize: '12px',
      fontWeight: '500',
      backgroundColor: style.bg,
      color: style.color,
    }}>
      {style.label}
    </span>
  );
};

// Sidebar Navigation Item
const NavItem = ({ icon: Icon, label, active, onClick, badge }) => (
  <button
    onClick={onClick}
    style={{
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      padding: '12px 16px',
      width: '100%',
      border: 'none',
      borderRadius: '10px',
      backgroundColor: active ? 'rgba(37, 99, 235, 0.1)' : 'transparent',
      color: active ? theme.primary : theme.textSecondary,
      cursor: 'pointer',
      transition: 'all 0.2s',
      fontFamily: "'DM Sans', sans-serif",
      fontSize: '14px',
      fontWeight: active ? '600' : '500',
    }}
  >
    <Icon size={20} />
    <span style={{ flex: 1, textAlign: 'left' }}>{label}</span>
    {badge && (
      <span style={{
        backgroundColor: theme.accentRed,
        color: 'white',
        fontSize: '11px',
        padding: '2px 8px',
        borderRadius: '10px',
      }}>{badge}</span>
    )}
  </button>
);

// Stats Card Component
const StatsCard = ({ icon: Icon, label, value, change, color }) => (
  <div style={{
    backgroundColor: 'white',
    borderRadius: '16px',
    padding: '24px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
    border: `1px solid ${theme.border}`,
  }}>
    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
      <div style={{
        width: '48px',
        height: '48px',
        borderRadius: '12px',
        backgroundColor: `${color}15`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        <Icon size={24} color={color} />
      </div>
      {change && (
        <span style={{
          fontSize: '12px',
          color: change > 0 ? theme.success : theme.accentRed,
          fontWeight: '500',
        }}>
          {change > 0 ? '+' : ''}{change}%
        </span>
      )}
    </div>
    <div style={{ marginTop: '16px' }}>
      <div style={{ fontSize: '28px', fontWeight: '700', color: theme.text, fontFamily: "'DM Sans', sans-serif" }}>
        {value}
      </div>
      <div style={{ fontSize: '13px', color: theme.textSecondary, marginTop: '4px' }}>
        {label}
      </div>
    </div>
  </div>
);

// AI Chat Window Component
const ChatWindow = ({ isOpen, onClose, messages }) => {
  const [input, setInput] = useState('');
  
  if (!isOpen) return null;
  
  return (
    <div style={{
      position: 'fixed',
      bottom: '100px',
      right: '24px',
      width: '400px',
      height: '550px',
      backgroundColor: theme.bgDark,
      borderRadius: '20px',
      boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      zIndex: 1000,
      animation: 'slideUp 0.3s ease-out',
    }}>
      {/* Header */}
      <div style={{
        background: `linear-gradient(135deg, ${theme.primary} 0%, #7C3AED 100%)`,
        padding: '20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '12px',
            backgroundColor: 'rgba(255,255,255,0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <span style={{ fontSize: '20px' }}>🤖</span>
          </div>
          <div>
            <div style={{ color: 'white', fontWeight: '600', fontSize: '16px' }}>5P AI Assistant</div>
            <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: '12px' }}>Paste tin nhắn từ Zalo → AI xử lý</div>
          </div>
        </div>
        <button onClick={onClose} style={{
          background: 'rgba(255,255,255,0.1)',
          border: 'none',
          borderRadius: '8px',
          padding: '8px',
          cursor: 'pointer',
          color: 'white',
        }}>
          <X size={20} />
        </button>
      </div>
      
      {/* Messages */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
      }}>
        {messages.map((msg, i) => (
          <div key={i} style={{
            alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: '85%',
          }}>
            {msg.role === 'user' ? (
              <div style={{
                backgroundColor: theme.primary,
                color: 'white',
                padding: '12px 16px',
                borderRadius: '16px 16px 4px 16px',
                fontSize: '14px',
              }}>
                <div style={{ fontSize: '11px', opacity: 0.7, marginBottom: '4px' }}>👤 Bạn • {msg.time}</div>
                {msg.content}
              </div>
            ) : (
              <div style={{
                backgroundColor: '#2D3748',
                padding: '16px',
                borderRadius: '16px 16px 16px 4px',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                  <span style={{ fontSize: '12px', color: '#A0AEC0' }}>🤖 AI • {msg.time || '18:19:17'}</span>
                  {msg.confirmed && (
                    <span style={{
                      backgroundColor: '#10B981',
                      color: 'white',
                      fontSize: '10px',
                      padding: '2px 8px',
                      borderRadius: '4px',
                    }}>✓ Đã xác nhận</span>
                  )}
                </div>
                
                {msg.intent && (
                  <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                    <span style={{
                      backgroundColor: theme.accentRed,
                      color: 'white',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      fontSize: '12px',
                      fontWeight: '600',
                    }}>{msg.intent}</span>
                    <span style={{
                      backgroundColor: '#4A5568',
                      color: 'white',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      fontSize: '12px',
                    }}>{msg.confidence}%</span>
                  </div>
                )}
                
                <div style={{
                  backgroundColor: '#1A202C',
                  padding: '12px',
                  borderRadius: '8px',
                  marginBottom: '12px',
                }}>
                  <div style={{ color: '#68D391', fontSize: '13px' }}>
                    ✅ Công việc {msg.job} đã hoàn thành
                  </div>
                </div>
                
                <div style={{ color: '#A0AEC0', fontSize: '13px' }}>
                  📊 Thông tin trích xuất:
                </div>
                <div style={{
                  backgroundColor: '#1A202C',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  marginTop: '8px',
                  fontFamily: 'monospace',
                  fontSize: '12px',
                  color: '#E2E8F0',
                }}>
                  job_number: {msg.job}
                </div>
                
                <div style={{
                  backgroundColor: '#276749',
                  color: '#68D391',
                  padding: '10px',
                  borderRadius: '6px',
                  marginTop: '12px',
                  fontSize: '13px',
                }}>
                  ✅ Đã xác nhận thành công!
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* Input */}
      <div style={{
        padding: '16px',
        borderTop: '1px solid #2D3748',
        display: 'flex',
        gap: '12px',
        alignItems: 'center',
      }}>
        <button style={{
          backgroundColor: '#2D3748',
          border: 'none',
          borderRadius: '10px',
          padding: '12px',
          cursor: 'pointer',
          color: '#A0AEC0',
        }}>
          <Paperclip size={20} />
        </button>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Paste tin nhắn hoặc ảnh (Ctrl+V)..."
          style={{
            flex: 1,
            backgroundColor: '#2D3748',
            border: 'none',
            borderRadius: '10px',
            padding: '12px 16px',
            color: 'white',
            fontSize: '14px',
            outline: 'none',
          }}
        />
        <button style={{
          background: `linear-gradient(135deg, ${theme.primary} 0%, #7C3AED 100%)`,
          border: 'none',
          borderRadius: '10px',
          padding: '12px 20px',
          cursor: 'pointer',
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontWeight: '500',
          fontSize: '14px',
        }}>
          <span>🚀</span> Gửi AI
        </button>
      </div>
    </div>
  );
};

// Floating AI Button
const FloatingAIButton = ({ onClick, hasNotification }) => (
  <button
    onClick={onClick}
    style={{
      position: 'fixed',
      bottom: '24px',
      right: '24px',
      width: '64px',
      height: '64px',
      borderRadius: '20px',
      border: 'none',
      background: `linear-gradient(135deg, ${theme.primary} 0%, #7C3AED 100%)`,
      boxShadow: '0 4px 20px rgba(37, 99, 235, 0.4)',
      cursor: 'pointer',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '2px',
      transition: 'transform 0.2s, box-shadow 0.2s',
      zIndex: 999,
    }}
  >
    <span style={{ fontSize: '24px' }}>🤖</span>
    <span style={{ color: 'white', fontSize: '10px', fontWeight: '600' }}>5P AI</span>
    {hasNotification && (
      <div style={{
        position: 'absolute',
        top: '-4px',
        right: '-4px',
        width: '20px',
        height: '20px',
        borderRadius: '10px',
        backgroundColor: theme.accentRed,
        color: 'white',
        fontSize: '11px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontWeight: '600',
      }}>2</div>
    )}
  </button>
);

// Main Dashboard Component
export default function SLMSDashboard() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [chatOpen, setChatOpen] = useState(false);
  const [activeNav, setActiveNav] = useState('dashboard');
  const { showTrucking, showWarehouse, showCustoms, showPacking } = useServiceVisibility();

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: theme.bgLight,
      fontFamily: "'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif",
    }}>
      {/* Google Fonts */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
      `}</style>

      {/* Sidebar */}
      <aside style={{
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
        width: sidebarOpen ? '260px' : '80px',
        backgroundColor: 'white',
        borderRight: `1px solid ${theme.border}`,
        transition: 'width 0.3s',
        zIndex: 100,
        display: 'flex',
        flexDirection: 'column',
      }}>
        {/* Logo */}
        <div style={{
          padding: '20px',
          borderBottom: `1px solid ${theme.border}`,
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
        }}>
          <div style={{
            width: '44px',
            height: '44px',
            background: `linear-gradient(135deg, ${theme.primary} 0%, ${theme.accent} 50%, ${theme.accentRed} 100%)`,
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <span style={{ color: 'white', fontWeight: '700', fontSize: '16px' }}>5P</span>
          </div>
          {sidebarOpen && (
            <div>
              <div style={{ fontWeight: '700', color: theme.accent, fontSize: '16px' }}>5P VIETNAM</div>
              <div style={{ fontSize: '11px', color: theme.primary, letterSpacing: '0.5px' }}>SLMS</div>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav style={{ flex: 1, padding: '16px 12px', overflowY: 'auto' }}>
          <NavItem icon={LayoutDashboard} label="Dashboard" active={activeNav === 'dashboard'} onClick={() => setActiveNav('dashboard')} />
          <NavItem icon={FileText} label="Jobs" active={activeNav === 'jobs'} onClick={() => setActiveNav('jobs')} badge="24" />
          
          <div style={{ height: '1px', backgroundColor: theme.border, margin: '16px 0' }} />
          <div style={{ fontSize: '11px', color: theme.textSecondary, padding: '0 16px', marginBottom: '8px', fontWeight: '600', letterSpacing: '0.5px' }}>
            SERVICES
          </div>
          
          {showTrucking && <NavItem icon={Truck} label="Trucking" active={activeNav === 'trucking'} onClick={() => setActiveNav('trucking')} badge="12" />}
          {showWarehouse && <NavItem icon={Warehouse} label="Warehouse" active={activeNav === 'warehouse'} onClick={() => setActiveNav('warehouse')} />}
          {showCustoms && <NavItem icon={FileText} label="Customs" active={activeNav === 'customs'} onClick={() => setActiveNav('customs')} />}
          {showPacking && <NavItem icon={Package} label="Packing" active={activeNav === 'packing'} onClick={() => setActiveNav('packing')} />}
          
          <div style={{ height: '1px', backgroundColor: theme.border, margin: '16px 0' }} />
          <div style={{ fontSize: '11px', color: theme.textSecondary, padding: '0 16px', marginBottom: '8px', fontWeight: '600', letterSpacing: '0.5px' }}>
            MANAGEMENT
          </div>
          
          <NavItem icon={Users} label="Master Data" active={activeNav === 'master'} onClick={() => setActiveNav('master')} />
          <NavItem icon={DollarSign} label="Financial" active={activeNav === 'financial'} onClick={() => setActiveNav('financial')} />
          <NavItem icon={BarChart3} label="Reports" active={activeNav === 'reports'} onClick={() => setActiveNav('reports')} />
        </nav>

        {/* Settings */}
        <div style={{ padding: '12px', borderTop: `1px solid ${theme.border}` }}>
          <NavItem icon={Settings} label="Settings" active={activeNav === 'settings'} onClick={() => setActiveNav('settings')} />
        </div>
      </aside>

      {/* Main Content */}
      <main style={{
        marginLeft: sidebarOpen ? '260px' : '80px',
        transition: 'margin-left 0.3s',
      }}>
        {/* Header */}
        <header style={{
          backgroundColor: 'white',
          borderBottom: `1px solid ${theme.border}`,
          padding: '16px 32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          position: 'sticky',
          top: 0,
          zIndex: 50,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <button onClick={() => setSidebarOpen(!sidebarOpen)} style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '8px',
              borderRadius: '8px',
              color: theme.textSecondary,
            }}>
              <Menu size={20} />
            </button>
            <div>
              <h1 style={{ fontSize: '20px', fontWeight: '700', color: theme.text }}>Dashboard</h1>
              <p style={{ fontSize: '13px', color: theme.textSecondary }}>Welcome back! Here's your logistics overview.</p>
            </div>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              backgroundColor: theme.bgLight,
              padding: '10px 16px',
              borderRadius: '10px',
              width: '280px',
            }}>
              <Search size={18} color={theme.textSecondary} />
              <input
                type="text"
                placeholder="Search jobs, customers..."
                style={{
                  border: 'none',
                  background: 'none',
                  outline: 'none',
                  fontSize: '14px',
                  color: theme.text,
                  width: '100%',
                }}
              />
            </div>
            
            <button style={{
              position: 'relative',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '10px',
              borderRadius: '10px',
              backgroundColor: theme.bgLight,
            }}>
              <Bell size={20} color={theme.textSecondary} />
              <span style={{
                position: 'absolute',
                top: '6px',
                right: '6px',
                width: '8px',
                height: '8px',
                borderRadius: '4px',
                backgroundColor: theme.accentRed,
              }} />
            </button>
            
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              background: `linear-gradient(135deg, ${theme.primary} 0%, ${theme.accent} 100%)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontWeight: '600',
              fontSize: '14px',
            }}>
              KH
            </div>
          </div>
        </header>

        {/* Dashboard Content */}
        <div style={{ padding: '32px' }}>
          {/* Stats Cards */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '24px',
            marginBottom: '32px',
          }}>
            <StatsCard icon={FileText} label="Jobs Today" value="24" change={12} color={theme.primary} />
            <StatsCard icon={Truck} label="Active Trucking" value="12" change={8} color={theme.accent} />
            <StatsCard icon={Warehouse} label="In Storage" value="156" change={-3} color="#8B5CF6" />
            <StatsCard icon={TrendingUp} label="Revenue MTD" value="1.2B" change={15} color={theme.success} />
          </div>

          {/* Charts and Tables Row */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1.5fr',
            gap: '24px',
          }}>
            {/* Jobs by Status */}
            <div style={{
              backgroundColor: 'white',
              borderRadius: '16px',
              padding: '24px',
              border: `1px solid ${theme.border}`,
            }}>
              <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '20px', color: theme.text }}>
                Jobs by Status
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {[
                  { label: 'Pending', value: 5, color: theme.warning },
                  { label: 'Confirmed', value: 8, color: theme.primary },
                  { label: 'In Transit', value: 6, color: '#8B5CF6' },
                  { label: 'Completed', value: 5, color: theme.success },
                ].map((item, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                      width: '12px',
                      height: '12px',
                      borderRadius: '3px',
                      backgroundColor: item.color,
                    }} />
                    <span style={{ flex: 1, fontSize: '14px', color: theme.textSecondary }}>{item.label}</span>
                    <span style={{ fontWeight: '600', color: theme.text }}>{item.value}</span>
                    <div style={{
                      width: '100px',
                      height: '6px',
                      backgroundColor: theme.border,
                      borderRadius: '3px',
                      overflow: 'hidden',
                    }}>
                      <div style={{
                        width: `${item.value * 10}%`,
                        height: '100%',
                        backgroundColor: item.color,
                        borderRadius: '3px',
                      }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Jobs */}
            <div style={{
              backgroundColor: 'white',
              borderRadius: '16px',
              padding: '24px',
              border: `1px solid ${theme.border}`,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '600', color: theme.text }}>Recent Jobs</h3>
                <button style={{
                  background: 'none',
                  border: 'none',
                  color: theme.primary,
                  fontSize: '13px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                }}>
                  View All <ChevronRight size={16} />
                </button>
              </div>
              
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: `1px solid ${theme.border}` }}>
                    {['Job No', 'Customer', 'Type', 'Time', 'Status'].map((h, i) => (
                      <th key={i} style={{
                        textAlign: 'left',
                        padding: '12px 8px',
                        fontSize: '12px',
                        fontWeight: '600',
                        color: theme.textSecondary,
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px',
                      }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {recentJobs.map((job, i) => (
                    <tr key={i} style={{
                      borderBottom: `1px solid ${theme.border}`,
                      cursor: 'pointer',
                      transition: 'background 0.2s',
                    }}>
                      <td style={{ padding: '14px 8px', fontWeight: '600', color: theme.primary, fontSize: '14px' }}>
                        {job.id}
                      </td>
                      <td style={{ padding: '14px 8px', fontSize: '14px', color: theme.text }}>{job.customer}</td>
                      <td style={{ padding: '14px 8px' }}>
                        <span style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          fontSize: '13px',
                          color: theme.textSecondary,
                        }}>
                          {job.type === 'trucking' && <Truck size={14} />}
                          {job.type === 'warehouse' && <Warehouse size={14} />}
                          {job.type === 'customs' && <FileText size={14} />}
                          {job.type === 'packing' && <Package size={14} />}
                          {job.type.charAt(0).toUpperCase() + job.type.slice(1)}
                        </span>
                      </td>
                      <td style={{ padding: '14px 8px', fontSize: '14px', color: theme.textSecondary }}>
                        {job.time}
                      </td>
                      <td style={{ padding: '14px 8px' }}>
                        <StatusBadge status={job.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>

      {/* Floating AI Button */}
      <FloatingAIButton onClick={() => setChatOpen(!chatOpen)} hasNotification={true} />
      
      {/* Chat Window */}
      <ChatWindow isOpen={chatOpen} onClose={() => setChatOpen(false)} messages={chatMessages} />
    </div>
  );
}
