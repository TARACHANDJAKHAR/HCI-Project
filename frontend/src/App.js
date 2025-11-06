/**
 * Elderly Care Assistant - React Frontend Application
 * 
 * Main React component for the voice assistant web interface.
 * Features:
 * - Voice input via Web Speech API
 * - Text input via keyboard
 * - Text-to-speech output
 * - Real-time chat interface
 * - Reminder and contact management
 * - Notification polling for scheduled reminders
 * 
 * Uses Tailwind CSS for styling and lucide-react for icons.
 */

import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Send, Phone, Clock, Heart, Bell, Volume2 } from 'lucide-react';

export default function ElderlyAssistant() {
  // ============================================================================
  // State Management
  // ============================================================================
  
  // Voice recognition state
  const [isListening, setIsListening] = useState(false);  // Is microphone active?
  const [transcript, setTranscript] = useState('');          // Current speech recognition result
  
  // Chat state
  const [messages, setMessages] = useState([]);             // Chat message history
  const [textInput, setTextInput] = useState('');            // Text input field value
  
  // UI state
  const [isSpeaking, setIsSpeaking] = useState(false);      // Is TTS currently speaking?
  const [assistantStarted, setAssistantStarted] = useState(false); // Has user started assistant?
  
  // Data state
  const [contacts, setContacts] = useState([]);             // Emergency contacts list
  const [reminders, setReminders] = useState([]);           // Reminders list (regular + scheduled)
  
  // Refs for DOM access and speech recognition
  const recognitionRef = useRef(null);                       // Web Speech API recognition instance
  const messagesEndRef = useRef(null);                      // Ref to scroll to bottom of chat
  
  // API base URL (Flask backend)
  const API_URL = 'http://localhost:5000/api';

  // ============================================================================
  // Initialization & Speech Recognition Setup
  // ============================================================================
  
  useEffect(() => {
    /**
     * Initialize Web Speech API for voice recognition.
     * 
     * Sets up speech recognition with:
     * - Continuous: false (stop after one result)
     * - Interim results: false (only final results)
     * - Language: en-IN (Indian English)
     * 
     * Handles recognition events:
     * - onresult: When speech is recognized
     * - onerror: When recognition fails
     * - onend: When recognition stops
     */
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      // Get SpeechRecognition API (Chrome uses webkit prefix)
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      
      // Configure recognition settings
      recognitionRef.current.continuous = false;      // Stop after one result
      recognitionRef.current.interimResults = false;  // Only final results (not interim)
      recognitionRef.current.lang = 'en-IN';          // Indian English

      // Handle successful recognition
      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setTranscript(transcript);
        // Process the recognized command
        handleCommand(transcript);
      };

      // Handle recognition errors
      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };

      // Handle recognition end
      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }

    // Load initial data on component mount
    fetchContacts();
    fetchReminders();
  }, []); // Empty dependency array = run once on mount

  // ============================================================================
  // Auto-scroll Chat
  // ============================================================================
  
  useEffect(() => {
    /**
     * Auto-scroll chat to bottom when new messages arrive.
     * 
     * Uses smooth scrolling for better UX.
     */
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]); // Run whenever messages change

  // ============================================================================
  // Notification Polling & Reminder Refresh
  // ============================================================================
  
  useEffect(() => {
    /**
     * Poll for reminder notifications and refresh reminders list.
     * 
     * This effect:
     * 1. Checks for notifications every 5 seconds
     * 2. Displays and speaks notifications when they arrive
     * 3. Refreshes reminders list every 30 seconds (every 6th check)
     * 
     * Notifications are triggered by the backend NotificationScheduler
     * when a scheduled reminder's time arrives.
     */
    let reminderRefreshCounter = 0;
    const notificationInterval = setInterval(async () => {
      try {
        // Check for notifications from backend
        const notifResponse = await fetch(`${API_URL}/notifications`);
        const notifData = await notifResponse.json();
        
        // If notifications exist, display and speak them
        if (notifData.notifications && notifData.notifications.length > 0) {
          notifData.notifications.forEach(notif => {
            const message = notif.message || `Reminder: ${notif.text}`;
            addMessage('assistant', message);
            speak(message);
          });
          // Refresh reminders after notification (to update UI)
          fetchReminders();
        }
        
        // Refresh reminders list periodically (every 30 seconds = every 6th check)
        reminderRefreshCounter++;
        if (reminderRefreshCounter >= 6) {
          fetchReminders();
          reminderRefreshCounter = 0;
        }
      } catch (error) {
        console.error('Error fetching notifications:', error);
      }
    }, 5000); // Check every 5 seconds

    // Cleanup: clear interval on component unmount
    return () => clearInterval(notificationInterval);
  }, []); // Empty dependency array = run once on mount

  // ============================================================================
  // Data Fetching Functions
  // ============================================================================
  
  /**
   * Fetch emergency contacts from backend.
   * 
   * Updates the contacts state with data from /api/contacts endpoint.
   */
  const fetchContacts = async () => {
    try {
      const response = await fetch(`${API_URL}/contacts`);
      const data = await response.json();
      setContacts(data.contacts || []);
    } catch (error) {
      console.error('Error fetching contacts:', error);
    }
  };

  /**
   * Fetch reminders from backend.
   * 
   * Updates the reminders state with data from /api/reminders endpoint.
   * Includes both regular and scheduled reminders (formatted).
   */
  const fetchReminders = async () => {
    try {
      const response = await fetch(`${API_URL}/reminders`);
      const data = await response.json();
      setReminders(data.reminders || []);
    } catch (error) {
      console.error('Error fetching reminders:', error);
    }
  };

  // ============================================================================
  // Text-to-Speech
  // ============================================================================
  
  /**
   * Speak text using Web Speech Synthesis API.
   * 
   * Cancels any ongoing speech before starting new speech to prevent overlap.
   * 
   * @param {string} text - Text to speak
   */
  const speak = (text) => {
    if ('speechSynthesis' in window) {
      // Cancel any ongoing speech to prevent overlapping
      window.speechSynthesis.cancel();
      setIsSpeaking(true);
      
      // Create speech utterance
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;    // Slightly slower for clarity
      utterance.pitch = 1;     // Normal pitch
      utterance.volume = 1;    // Full volume
      utterance.lang = 'en-IN'; // Indian English
      
      // Handle speech end
      utterance.onend = () => setIsSpeaking(false);
      
      // Handle speech errors
      utterance.onerror = (e) => console.error('TTS Error:', e.error);
      
      // Start speaking
      window.speechSynthesis.speak(utterance);
    }
  };

  // ============================================================================
  // Message Management
  // ============================================================================
  
  /**
   * Add a message to the chat history.
   * 
   * @param {string} type - Message type: 'user' or 'assistant'
   * @param {string} content - Message text content
   */
  const addMessage = (type, content) => {
    setMessages((prev) => [...prev, { type, content, timestamp: new Date() }]);
  };

  // ============================================================================
  // Command Processing
  // ============================================================================
  
  /**
   * Handle user command (from voice or text input).
   * 
   * Sends command to backend API, receives response, and:
   * 1. Adds user message to chat
   * 2. Adds assistant response to chat
   * 3. Speaks the response
   * 4. Refreshes reminders/contacts if command was related
   * 
   * @param {string} command - User's command text
   */
  const handleCommand = async (command) => {
    // Add user message to chat
    addMessage('user', command);

    try {
      // Send command to backend API
      const response = await fetch(`${API_URL}/process-command`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command }),
      });

      const data = await response.json();

      // If response exists, display and speak it
      if (data.response) {
        addMessage('assistant', data.response);
        speak(data.response);
      }

      // Refresh reminders/contacts if command was related to them
      // This ensures UI stays in sync after changes
      if (command.includes('reminder') || command.includes('contact') || 
          command.includes('delete') || command.includes('remove') || command.includes('clear')) {
        fetchReminders();
        fetchContacts();
      }
    } catch (error) {
      // Handle errors gracefully
      const errorMsg = 'Sorry, I had trouble processing that.';
      addMessage('assistant', errorMsg);
      speak(errorMsg);
    }
  };

  // ============================================================================
  // Voice Input Controls
  // ============================================================================
  
  /**
   * Toggle voice recognition on/off.
   * 
   * Starts or stops the Web Speech API recognition.
   * Shows error alert if speech recognition is not supported.
   */
  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not supported in your browser');
      return;
    }

    if (isListening) {
      // Stop recognition
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      // Start recognition
      setTranscript('');
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  // ============================================================================
  // Text Input Controls
  // ============================================================================
  
  /**
   * Handle text input submission (Enter key or Send button).
   * 
   * Processes the text input as a command and clears the input field.
   */
  const handleTextSubmit = () => {
    if (textInput.trim()) {
      handleCommand(textInput);
      setTextInput(''); // Clear input after sending
    }
  };

  /**
   * Handle Enter key press in text input.
   * 
   * @param {KeyboardEvent} e - Keyboard event
   */
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') handleTextSubmit();
  };

  // ============================================================================
  // UI Components
  // ============================================================================
  
  /**
   * Quick Action Button Component
   * 
   * Reusable button for quick actions (Time, Weather, Reminders, Emergency).
   * 
   * @param {Object} props - Component props
   * @param {React.Component} props.icon - Icon component from lucide-react
   * @param {string} props.label - Button label text
   * @param {string} props.command - Command to send when clicked
   */
  const QuickAction = ({ icon: Icon, label, command }) => (
    <button
      onClick={() => handleCommand(command)}
      className="flex flex-col items-center justify-center p-4 bg-white rounded-xl shadow-md hover:shadow-lg transition-all hover:scale-105"
    >
      <Icon className="w-8 h-8 mb-2 text-blue-600" />
      <span className="text-sm font-medium text-gray-700">{label}</span>
    </button>
  );

  // ============================================================================
  // Render
  // ============================================================================
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header Section */}
        <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-800 text-center mb-2">
            Elderly Care Assistant
          </h1>
          <p className="text-gray-600 text-center">Your friendly voice companion</p>

          {/* Start Assistant Button - Only shown before assistant starts */}
          {!assistantStarted && (
            <div className="text-center mt-6">
              <button
                onClick={() => {
                  // Initialize assistant with greeting
                  addMessage('assistant', 'Hello! I am your elderly care assistant. How can I help you?');
                  speak('Hello! I am your elderly care assistant. How can I help you?');
                  setAssistantStarted(true);
                }}
                className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors"
              >
                Start Assistant
              </button>
            </div>
          )}
        </div>

        {/* Main Content - Only shown after assistant starts */}
        {assistantStarted && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column: Quick Actions & Chat */}
            <div className="lg:col-span-2">
              {/* Quick Actions Panel */}
              <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
                <h2 className="text-xl font-semibold text-gray-800 mb-4">Quick Actions</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <QuickAction icon={Clock} label="Time" command="what time is it" />
                  <QuickAction icon={Heart} label="Weather" command="what's the weather" />
                  <QuickAction icon={Bell} label="Reminders" command="list reminders" />
                  <QuickAction icon={Phone} label="Emergency" command="emergency help" />
                </div>
              </div>

              {/* Chat Interface */}
              <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
                {/* Messages Display Area */}
                <div className="h-96 overflow-y-auto mb-4 space-y-4">
                  {messages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-xs md:max-w-md px-4 py-3 rounded-2xl ${
                          msg.type === 'user'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {/* Message content with whitespace-pre-wrap to preserve line breaks */}
                        <p className="text-base whitespace-pre-wrap">{msg.content}</p>
                        {/* Timestamp */}
                        <span className="text-xs opacity-70 mt-1 block">
                          {msg.timestamp.toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  ))}
                  {/* Invisible element to scroll to */}
                  <div ref={messagesEndRef} />
                </div>

                {/* Input Controls */}
                <div className="flex items-center gap-4">
                  {/* Voice Input Button */}
                  <button
                    onClick={toggleListening}
                    className={`p-4 rounded-full transition-all ${
                      isListening
                        ? 'bg-red-500 hover:bg-red-600 animate-pulse'
                        : 'bg-blue-600 hover:bg-blue-700'
                    } text-white shadow-lg`}
                  >
                    {isListening ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
                  </button>

                  {/* Text Input & Send Button */}
                  <div className="flex-1 flex gap-2">
                    <input
                      type="text"
                      value={textInput}
                      onChange={(e) => setTextInput(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Type your message..."
                      className="flex-1 px-4 py-3 border-2 border-gray-300 rounded-xl focus:outline-none focus:border-blue-500 text-lg"
                    />
                    <button
                      onClick={handleTextSubmit}
                      className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors"
                    >
                      <Send className="w-5 h-5" />
                    </button>
                  </div>
                </div>

                {/* Status Indicators */}
                {isListening && (
                  <p className="text-center text-blue-600 mt-2 font-medium">
                    Listening... {transcript}
                  </p>
                )}

                {isSpeaking && (
                  <div className="flex items-center justify-center gap-2 text-green-600 mt-2">
                    <Volume2 className="w-5 h-5 animate-pulse" />
                    <span className="font-medium">Speaking...</span>
                  </div>
                )}
              </div>
            </div>

            {/* Right Column: Reminders & Contacts */}
            <div className="space-y-6">
              {/* Reminders Panel */}
              <div className="bg-white rounded-2xl shadow-xl p-6">
                <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
                  <Bell className="w-5 h-5 text-blue-600" />
                  Reminders
                </h2>
                <div className="space-y-2">
                  {reminders.length > 0 ? (
                    reminders.map((reminder, idx) => (
                      <div key={idx} className="p-3 bg-blue-50 rounded-lg">
                        <p className="text-gray-700">{reminder}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-500 text-sm">No reminders set</p>
                  )}
                </div>
              </div>

              {/* Emergency Contacts Panel */}
              <div className="bg-white rounded-2xl shadow-xl p-6">
                <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
                  <Phone className="w-5 h-5 text-red-600" />
                  Emergency Contacts
                </h2>
                <div className="space-y-2">
                  {contacts.length > 0 ? (
                    contacts.map((contact, idx) => (
                      <div key={idx} className="p-3 bg-red-50 rounded-lg">
                        <p className="font-medium text-gray-800">{contact.name}</p>
                        <p className="text-sm text-gray-600">{contact.phone}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-500 text-sm">No contacts added</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
