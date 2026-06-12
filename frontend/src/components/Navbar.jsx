import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShieldAlert, User as UserIcon, LogOut, Settings, ChevronDown } from 'lucide-react';
import EditProfileModal from './EditProfileModal';

const UserDropdown = ({ isProfileOpen, setIsProfileOpen, user, setIsEditModalOpen, handleLogout }) => (
  <div className="relative">
    <button 
      onClick={() => setIsProfileOpen(!isProfileOpen)} 
      className="flex items-center gap-1.5 bg-nature-50 border border-nature-200 px-3 py-1.5 rounded-full text-nature-700 hover:bg-nature-100 transition-colors shadow-sm"
    >
      <UserIcon className="w-4 h-4" />
      <span className="text-xs font-bold hidden sm:block">{user.name.split(' ')[0]}</span>
      <span className="text-xs font-bold sm:hidden">Profile</span>
      <ChevronDown className={`w-3 h-3 transition-transform ${isProfileOpen ? 'rotate-180' : ''}`} />
    </button>
    
    {isProfileOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-lg py-1 border border-gray-100 z-50 animate-in fade-in zoom-in duration-200 origin-top-right">
            <div className="px-4 py-2 border-b border-gray-50">
                <p className="text-sm font-semibold text-gray-900 truncate">{user.name}</p>
                <p className="text-xs text-gray-500 capitalize">{user.role}</p>
            </div>
            <button 
                onClick={() => { setIsEditModalOpen(true); setIsProfileOpen(false); }}
                className="w-full text-left px-4 py-2 text-sm flex items-center gap-2 text-gray-700 hover:bg-nature-50 hover:text-nature-700 transition-colors"
            >
                <Settings className="w-4 h-4" />
                Edit Profile
            </button>
            <button 
                onClick={handleLogout}
                className="w-full text-left px-4 py-2 text-sm flex items-center gap-2 text-red-600 hover:bg-red-50 transition-colors"
            >
                <LogOut className="w-4 h-4" />
                Logout
            </button>
        </div>
    )}
  </div>
);

const Navbar = () => {
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const navigate = useNavigate();
  const storedUser = localStorage.getItem('user');
  const user = storedUser ? JSON.parse(storedUser) : null;
  const isAdmin = user && user.role === 'admin';

  const handleLogout = () => {
    localStorage.removeItem('user');
    setIsProfileOpen(false);
    navigate('/login');
  };

  const handleSaveSuccess = () => {
    // The location hook will not automatically trigger a re-render if the path doesn't change.
    // By keeping user state strictly from localStorage inside the render cycle, it updates.
    // However, to force a refresh of the navbar, we can trigger a re-render or rely on the parent.
    // A simpler way: we'll let the user state be derived from localStorage, and closing the modal
    // forces a re-render of Navbar.
    setIsEditModalOpen(false);
  };

  return (
    <>
      <nav className="bg-white/80 backdrop-blur-md shadow-sm fixed w-full z-50 top-0 border-b border-gray-100">
        <div className="w-full px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center space-x-2">
              <ShieldAlert className="h-8 w-8 text-nature-600" />
              <span className="font-bold text-lg text-gray-800 tracking-tight flex-shrink-0 mr-4">AI Wildlife Alerts</span>
            </Link>
            
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                <Link to="/dashboard" className="text-gray-600 hover:text-nature-600 px-3 py-2 rounded-md text-sm font-medium transition-colors">Live Dashboard</Link>
                <Link to="/report" className="text-gray-600 hover:text-nature-600 px-3 py-2 rounded-md text-sm font-medium transition-colors">Report Incident</Link>
                {isAdmin && (
                    <Link to="/admin/users" className="text-purple-600 hover:text-purple-700 bg-purple-50 px-3 py-2 rounded-md text-sm font-bold transition-colors border border-purple-100">Users Directory</Link>
                )}
                {!user ? (
                    <>
                        <Link to="/register" className="text-gray-600 hover:text-nature-600 px-3 py-2 rounded-md text-sm font-medium transition-colors">Register</Link>
                        <Link to="/login" className="bg-nature-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-nature-700 transition-colors shadow-sm hover:shadow-md">Login</Link>
                    </>
                ) : (
                    <UserDropdown 
                      isProfileOpen={isProfileOpen} 
                      setIsProfileOpen={setIsProfileOpen} 
                      user={user} 
                      setIsEditModalOpen={setIsEditModalOpen} 
                      handleLogout={handleLogout} 
                    />
                )}
              </div>
            </div>

            <div className="md:hidden flex items-center">
              {user ? (
                <UserDropdown 
                  isProfileOpen={isProfileOpen} 
                  setIsProfileOpen={setIsProfileOpen} 
                  user={user} 
                  setIsEditModalOpen={setIsEditModalOpen} 
                  handleLogout={handleLogout} 
                />
              ) : (
                <Link to="/login" className="flex items-center gap-1.5 bg-nature-50 border border-nature-200 px-3 py-1.5 rounded-full text-nature-700 hover:bg-nature-100 transition-colors shadow-sm">
                  <UserIcon className="w-4 h-4" />
                  <span className="text-xs font-bold">Profile</span>
                </Link>
              )}
            </div>
          </div>
        </div>
      </nav>
      
      {/* Edit Profile Modal */}
      <EditProfileModal 
        isOpen={isEditModalOpen} 
        onClose={() => setIsEditModalOpen(false)} 
        user={user} 
        onSaveSuccess={handleSaveSuccess} 
      />
    </>
  );
};

export default Navbar;
