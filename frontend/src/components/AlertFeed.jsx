import React, { useEffect, useState, useRef, useCallback } from 'react';
import { MapPin, Clock, AlertTriangle, ShieldAlert, AlertOctagon, Flame, Edit2, Trash2, X, Check, Volume2, VolumeX } from 'lucide-react';
import CampusMap from './CampusMap';

const AlertCard = ({ alert, isAdmin, onDelete, onUpdate }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editDesc, setEditDesc] = useState(alert.description);
  const [editLevel, setEditLevel] = useState(alert.alert_level || 'Info');

  const isEmergency = alert.alert_level === 'Emergency';
  const isWarning = alert.alert_level === 'Warning';
  
  const badgeColors = isEmergency 
    ? "bg-red-100 text-red-800 border-red-200" 
    : isWarning 
      ? "bg-orange-100 text-orange-800 border-orange-200"
      : "bg-blue-100 text-blue-800 border-blue-200";

  const Icon = isEmergency ? AlertOctagon : isWarning ? AlertTriangle : ShieldAlert;

  const handleSave = () => {
      onUpdate(alert.id, { description: editDesc, alert_level: editLevel });
      setIsEditing(false);
  };

  if (isEditing) {
      return (
        <div className="bg-white rounded-2xl shadow-sm border border-nature-300 overflow-hidden p-5">
            <h3 className="text-lg font-bold mb-4 text-nature-800">Edit Alert</h3>
            <div className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700">Description</label>
                    <input 
                        type="text" 
                        value={editDesc} 
                        onChange={e => setEditDesc(e.target.value)}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700">Alert Level</label>
                    <select 
                        value={editLevel} 
                        onChange={e => setEditLevel(e.target.value)}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                    >
                        <option value="Info">Info</option>
                        <option value="Warning">Warning</option>
                        <option value="Emergency">Emergency</option>
                    </select>
                </div>
                <div className="flex gap-2 justify-end mt-4">
                    <button onClick={() => setIsEditing(false)} className="px-3 py-1.5 flex items-center gap-1 text-sm text-gray-600 bg-gray-100 rounded hover:bg-gray-200">
                        <X className="w-4 h-4" /> Cancel
                    </button>
                    <button onClick={handleSave} className="px-3 py-1.5 flex items-center gap-1 text-sm text-white bg-nature-600 rounded hover:bg-nature-700">
                        <Check className="w-4 h-4" /> Save
                    </button>
                </div>
            </div>
        </div>
      );
  }

  return (
    <div className={`bg-white rounded-2xl shadow-sm border ${isEmergency ? 'border-red-200 shadow-red-100' : 'border-gray-100'} overflow-hidden`}>
      <div className="flex flex-col sm:flex-row">
        {/* Mobile Full-width Image, desktop left-aligned */}
        <div className="w-full sm:w-48 h-48 sm:h-auto shrink-0 relative">
          <img
            className="w-full h-full object-cover"
            src={alert.image_url || "https://images.unsplash.com/photo-1546182990-dced71875059?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80"}
            alt={alert.description}
          />
          <div className="absolute top-2 right-2 sm:hidden flex gap-2">
            <span className={`px-2.5 py-1 text-xs font-bold rounded-full border ${badgeColors} backdrop-blur-md`}>
              {alert.alert_level || 'Alert'}
            </span>
          </div>
        </div>
        
        <div className="p-5 flex-1 relative">
          <div className="hidden sm:flex absolute top-5 right-5 gap-2">
            <span className={`px-3 py-1 text-xs font-bold rounded-full border ${badgeColors} flex items-center shadow-sm`}>
              <Icon className="w-3.5 h-3.5 mr-1" />
              {alert.alert_level || 'Alert'}
            </span>
          </div>

          <div className="text-sm font-bold text-gray-500 tracking-wider uppercase flex items-center gap-1.5 mb-1">
             AI DETECTED: <span className="text-gray-900">{alert.species || 'Unknown'}</span>
          </div>
          
          <h3 className="text-lg font-bold text-gray-900 leading-tight mb-2">
            {alert.description}
          </h3>
          
          <div className="space-y-2 mt-4 text-sm text-gray-600">
            <div className="flex items-center">
              <div className="w-6 h-6 rounded-full bg-gray-50 flex items-center justify-center mr-2">
                 <MapPin className="w-3.5 h-3.5 text-gray-400" />
              </div>
              <span className="font-medium text-gray-800">{alert.location}</span>
            </div>
            {alert.distance > 0 && (
              <div className="flex items-center">
                <div className="w-6 h-6 rounded-full bg-gray-50 flex items-center justify-center mr-2">
                   <ShieldAlert className="w-3.5 h-3.5 text-gray-400" />
                </div>
                <span>Distance approx. <strong className="text-gray-800">{alert.distance}m</strong></span>
              </div>
            )}
            <div className="flex items-center">
              <div className="w-6 h-6 rounded-full bg-gray-50 flex items-center justify-center mr-2">
                 <Clock className="w-3.5 h-3.5 text-gray-400" />
              </div>
              <span className="font-medium text-gray-700">
                {new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                <span className="mx-2 text-gray-300">|</span>
                {new Date(alert.timestamp).toLocaleDateString([], { day: '2-digit', month: 'short' })}
              </span>
            </div>
          </div>
          
          {isAdmin && (
            <div className="absolute bottom-5 right-5 flex gap-2">
                <button onClick={() => setIsEditing(true)} className="p-2 text-gray-500 hover:text-nature-600 hover:bg-nature-50 rounded-full transition-colors" title="Edit Alert">
                    <Edit2 className="w-4 h-4" />
                </button>
                <button onClick={() => onDelete(alert.id)} className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-full transition-colors" title="Delete Alert">
                    <Trash2 className="w-4 h-4" />
                </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const HotZonesWidget = ({ hotzones }) => {
    if (!hotzones || hotzones.length === 0) return null;
    
    return (
        <div className="bg-white rounded-2xl shadow-sm border border-orange-100 p-5 mb-6">
            <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2 mb-4">
                <Flame className="w-5 h-5 text-orange-500" />
                Activity Hot Zones
            </h3>
            <div className="flex overflow-x-auto pb-2 gap-3 snap-x">
                {hotzones.map((zone, idx) => (
                    <div key={idx} className="snap-start shrink-0 bg-orange-50/50 border border-orange-100 rounded-xl p-3 min-w-[140px]">
                        <div className="text-orange-600 font-bold text-2xl leading-none mb-1">{zone.incident_count}</div>
                        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Incidents</div>
                        <div className="text-sm font-medium text-gray-900 mt-2 truncate w-full" title={zone.location}>{zone.location}</div>
                    </div>
                ))}
            </div>
        </div>
    );
};

const speakAlert = (alert) => {
    console.log("DEBUG: Attempting to speak alert:", alert.id);
    
    // On mobile, the speech engine can get 'stuck'. Resume is needed.
    if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
    }

    const timeStr = new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const message = `Attention! ${alert.species || 'Animal'} detected at ${alert.location} at ${timeStr}. ${alert.description}`;
    const utterance = new SpeechSynthesisUtterance(message);
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 1;

    // Optional: select a voice (mobile browsers often have specific ones)
    const voices = window.speechSynthesis.getVoices();
    if (voices.length > 0) {
        utterance.voice = voices.find(v => v.lang.includes('en')) || voices[0];
    }

    window.speechSynthesis.speak(utterance);
};

const AlertFeed = () => {
    const [alerts, setAlerts] = useState([]);
    const [hotzones, setHotzones] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isVoiceEnabled, setIsVoiceEnabled] = useState(() => {
        return localStorage.getItem('voiceAlerts') === 'true';
    });
    const lastSpokenIdRef = useRef(localStorage.getItem('lastSpokenId'));
    const lastSpeakTimeRef = useRef(0);
    
    // Check if the current user is an admin
    const storedUser = localStorage.getItem('user');
    const user = storedUser ? JSON.parse(storedUser) : null;
    const isAdmin = user && user.role === 'admin';

    const fetchData = useCallback(async () => {
        try {
            const [alertsRes, hotzonesRes] = await Promise.all([
                fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'}/api/alerts`),
                fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'}/api/hotzones`)
            ]);
            
            if (alertsRes.ok) {
                const newAlerts = await alertsRes.json();
                
                // Voice Alert Logic
                if (newAlerts.length > 0) {
                    const latest = newAlerts[0];
                    
                    // Trigger voice if:
                    // 1. Voice is ON
                    // 2. This alert ID hasn't been spoken yet (checked via Ref for sync safety)
                    // 3. The alert is from today (within 12 hours)
                    // 4. We haven't spoken in the last 15 seconds (prevents spamming)
                    const alertTime = new Date(latest.timestamp).getTime();
                    const now = new Date().getTime();
                    const isToday = (now - alertTime) < 12 * 60 * 60 * 1000;
                    const enoughTimePassed = (now - lastSpeakTimeRef.current) > 15000;

                    if (isVoiceEnabled && latest.id.toString() !== lastSpokenIdRef.current && isToday && enoughTimePassed) {
                        console.log("DEBUG: TRIGGERING VOICE ALERT for ID:", latest.id);
                        lastSpokenIdRef.current = latest.id.toString();
                        localStorage.setItem('lastSpokenId', latest.id.toString());
                        lastSpeakTimeRef.current = now;
                        speakAlert(latest);
                    }
                }
                
                setAlerts(newAlerts);
            }
            if (hotzonesRes.ok) setHotzones(await hotzonesRes.json());
        } catch (error) {
            console.error("Error fetching data:", error);
        } finally {
            setLoading(false);
        }
    }, [isVoiceEnabled]);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000); // Fast poll for real-time mobile feel
        return () => clearInterval(interval);
    }, [fetchData]);

    const toggleVoice = () => {
        if (!isVoiceEnabled) {
            console.log("DEBUG: Voice alerts enabled. Warming up...");
            // Non-silent warm up so user knows it's working
            const msg = new SpeechSynthesisUtterance("Voice alerts activated");
            msg.volume = 1; 
            window.speechSynthesis.speak(msg);
        } else {
            console.log("DEBUG: Voice alerts disabled.");
            window.speechSynthesis.cancel();
        }
        const newState = !isVoiceEnabled;
        setIsVoiceEnabled(newState);
        localStorage.setItem('voiceAlerts', newState);
    };

    const handleDelete = async (id) => {
        if (!window.confirm('Are you sure you want to delete this alert?')) return;
        try {
            const res = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'}/api/alerts/${id}`, { method: 'DELETE' });
            if (res.ok) {
                setAlerts(alerts.filter(a => a.id !== id));
                // Optional: refresh hotzones
                fetchData();
            } else {
                alert('Failed to delete alert');
            }
        } catch (e) {
            console.error(e);
        }
    };

    const handleUpdate = async (id, updatedData) => {
        try {
            const res = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'}/api/alerts/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatedData)
            });
            if (res.ok) {
                const data = await res.json();
                setAlerts(alerts.map(a => a.id === id ? data.alert : a));
                fetchData(); // refresh hotzones
            } else {
                alert('Failed to update alert');
            }
        } catch (e) {
            console.error(e);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[50vh] text-gray-500">
                <div className="animate-pulse flex flex-col items-center">
                    <ShieldAlert className="h-10 w-10 text-gray-300 mb-2" />
                    Connecting to Edge Network...
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-3xl mx-auto px-4 py-6 sm:py-8">
            <div className="mb-6 flex justify-between items-start">
                <div>
                    <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight">Real-Time Alerts</h1>
                    <p className="text-sm text-gray-500 mt-1">Live feed from AI perimeter cameras</p>
                </div>
                <div className="flex flex-col items-end gap-2">
                    <button 
                        onClick={toggleVoice}
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold transition-all shadow-sm
                            ${isVoiceEnabled 
                                ? 'bg-nature-600 text-white hover:bg-nature-700' 
                                : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}
                    >
                        {isVoiceEnabled ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
                        {isVoiceEnabled ? 'Voice Alerts ON' : 'Voice Alerts OFF'}
                    </button>
                    {alerts.length > 0 && (
                        <div className="flex items-center text-[10px] font-bold text-green-600 bg-green-50 px-2 py-0.5 rounded-full animate-pulse">
                            <span className="w-1.5 h-1.5 rounded-full bg-green-600 mr-1.5 flex-shrink-0"></span> LIVE
                        </div>
                    )}
                </div>
            </div>

            <CampusMap hotzones={hotzones} />
            
            {/* Telegram Join Banner */}
            <div className="bg-blue-50 border border-blue-100 rounded-2xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4 mb-6">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-[#0088cc] rounded-full flex items-center justify-center shrink-0">
                        <svg className="w-5 h-5 fill-white" viewBox="0 0 24 24"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.295-.6.295-.002 0-.003 0-.005 0l.213-3.054 5.56-5.022c.24-.213-.054-.334-.373-.121l-6.869 4.326-2.96-.924c-.64-.203-.658-.64.135-.954l11.566-4.458c.538-.196 1.006.128.832.94z"/></svg>
                    </div>
                    <div>
                        <h3 className="text-blue-900 font-bold text-sm sm:text-base">Get Instant Mobile Alerts</h3>
                        <p className="text-blue-700 text-xs sm:text-sm">Join our Telegram channel to receive real-time notifications.</p>
                    </div>
                </div>
                <a href="https://t.me/+fAHbyw9iIu42YTU1" target="_blank" rel="noopener noreferrer" className="w-full sm:w-auto text-center px-5 py-2.5 bg-[#0088cc] hover:bg-[#0077b5] text-white font-semibold rounded-xl text-sm transition-colors shadow-sm shrink-0">
                    Join Telegram Alerts Channel
                </a>
            </div>

            <HotZonesWidget hotzones={hotzones} />

            <div className="space-y-4 sm:space-y-6">
                {alerts.length === 0 ? (
                    <div className="text-center py-16 bg-white rounded-2xl border border-dashed border-gray-200">
                        <ShieldAlert className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                        <p className="text-gray-500 font-medium">No activity detected.</p>
                        <p className="text-gray-400 text-sm mt-1">AI cameras are actively monitoring.</p>
                    </div>
                ) : (
                    alerts.map(alert => (
                        <AlertCard 
                            key={alert.id} 
                            alert={alert} 
                            isAdmin={isAdmin} 
                            onDelete={handleDelete}
                            onUpdate={handleUpdate}
                        />
                    ))
                )}
            </div>
        </div>
    );
};

export default AlertFeed;
