import React, { useEffect, useState } from 'react';
import { AlertOctagon, AlertTriangle, ShieldAlert, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const GlobalNotification = () => {
    const [latestAlert, setLatestAlert] = useState(null);
    const [lastSeenAlertId, setLastSeenAlertId] = useState(null);
    const [visible, setVisible] = useState(false);
    const navigate = useNavigate();

    // 1. On mount, fetch alerts to get the baseline ID
    useEffect(() => {
        const initFetch = async () => {
            try {
                const res = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'}/api/alerts`);
                if (res.ok) {
                    const data = await res.json();
                    if (data.length > 0) {
                        setLastSeenAlertId(data[0].id);
                    } else {
                        setLastSeenAlertId(0);
                    }
                }
            } catch (e) {
                console.error("Init fetch error", e);
            }
        };
        initFetch();
    }, []);

    // 2. Poll every 5 seconds for IDs greater than lastSeenAlertId
    useEffect(() => {
        if (lastSeenAlertId === null) return;

        const interval = setInterval(async () => {
            try {
                const res = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'}/api/alerts`);
                if (res.ok) {
                    const data = await res.json();
                    if (data.length > 0) {
                        const topAlert = data[0];
                        if (topAlert.id > lastSeenAlertId) {
                            setLatestAlert(topAlert);
                            setVisible(true);
                            setLastSeenAlertId(topAlert.id);
                            
                            // Auto dismiss after 10 seconds
                            setTimeout(() => setVisible(false), 10000);
                        }
                    }
                }
            } catch {
                // Silently handle polling errors to avoid console spam if offline
            }
        }, 5000);

        return () => clearInterval(interval);
    }, [lastSeenAlertId]);

    if (!visible || !latestAlert) return null;

    const isEmergency = latestAlert.alert_level === 'Emergency';
    const isWarning = latestAlert.alert_level === 'Warning';
    
    let bgColor = "border-blue-500";
    let iconColor = "text-blue-500";
    let Icon = ShieldAlert;

    if (isEmergency) {
        bgColor = "border-red-500";
        iconColor = "text-red-500";
        Icon = AlertOctagon;
    } else if (isWarning) {
        bgColor = "border-orange-500";
        iconColor = "text-orange-500";
        Icon = AlertTriangle;
    }

    return (
        <div className="fixed top-20 left-4 right-4 sm:left-auto sm:right-6 lg:right-8 z-50 animate-in slide-in-from-top-5 fade-in duration-300">
            <div className={`max-w-sm w-full shadow-2xl rounded-xl pointer-events-auto border-l-4 ${bgColor} bg-white overflow-hidden ring-1 ring-black ring-opacity-5`}>
                <div className="p-4">
                    <div className="flex items-start">
                        <div className="flex-shrink-0 mt-0.5">
                            <Icon className={`h-6 w-6 ${iconColor}`} />
                        </div>
                        <div className="ml-3 w-0 flex-1 pt-0.5">
                            <p className={`text-sm font-bold ${isEmergency ? 'text-red-700' : isWarning ? 'text-orange-700' : 'text-blue-700'}`}>
                                {latestAlert.alert_level ? `${latestAlert.alert_level.toUpperCase()} ALERT` : 'NEW ALERT'}
                            </p>
                            <p className="mt-1 text-sm text-gray-700 font-medium">
                                {latestAlert.description}
                            </p>
                            <p className="mt-1 text-sm text-gray-500">
                                {latestAlert.location}
                            </p>
                            <div className="mt-3 flex space-x-7">
                                <button
                                    type="button"
                                    className={`bg-white rounded-md text-sm font-bold ${iconColor} hover:underline focus:outline-none`}
                                    onClick={() => {
                                        setVisible(false);
                                        navigate('/dashboard');
                                    }}
                                >
                                    View on Map
                                </button>
                                <button
                                    type="button"
                                    className="bg-white rounded-md text-sm font-medium text-gray-500 hover:text-gray-700 focus:outline-none"
                                    onClick={() => setVisible(false)}
                                >
                                    Dismiss
                                </button>
                            </div>
                        </div>
                        <div className="ml-4 flex-shrink-0 flex">
                            <button
                                className="bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none"
                                onClick={() => setVisible(false)}
                            >
                                <span className="sr-only">Close</span>
                                <X className="h-5 w-5" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default GlobalNotification;
