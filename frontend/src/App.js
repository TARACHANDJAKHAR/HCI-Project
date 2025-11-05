import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Send, Phone, Clock, Heart, Bell, Volume2 } from 'lucide-react';

export default function ElderlyAssistant() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [messages, setMessages] = useState([]);
  const [textInput, setTextInput] = useState('');
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [contacts, setContacts] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [assistantStarted, setAssistantStarted] = useState(false); // ✅ new state

  const recognitionRef = useRef(null);
  const messagesEndRef = useRef(null);
  const API_URL = 'http://localhost:5000/api';

  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-IN';

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setTranscript(transcript);
        handleCommand(transcript);
      };

      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }

    fetchContacts();
    fetchReminders();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchContacts = async () => {
    try {
      const response = await fetch(`${API_URL}/contacts`);
      const data = await response.json();
      setContacts(data.contacts || []);
    } catch (error) {
      console.error('Error fetching contacts:', error);
    }
  };

  const fetchReminders = async () => {
    try {
      const response = await fetch(`${API_URL}/reminders`);
      const data = await response.json();
      setReminders(data.reminders || []);
    } catch (error) {
      console.error('Error fetching reminders:', error);
    }
  };

  const speak = (text) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel(); // ✅ prevent overlapping speech
      setIsSpeaking(true);
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1;
      utterance.volume = 1;
      utterance.lang = 'en-IN';
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = (e) => console.error('TTS Error:', e.error);
      window.speechSynthesis.speak(utterance);
    }
  };

  const addMessage = (type, content) => {
    setMessages((prev) => [...prev, { type, content, timestamp: new Date() }]);
  };

  const handleCommand = async (command) => {
    addMessage('user', command);

    try {
      const response = await fetch(`${API_URL}/process-command`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command }),
      });

      const data = await response.json();

      if (data.response) {
        addMessage('assistant', data.response);
        speak(data.response);
      }

      if (command.includes('reminder') || command.includes('contact')) {
        fetchReminders();
        fetchContacts();
      }
    } catch (error) {
      const errorMsg = 'Sorry, I had trouble processing that.';
      addMessage('assistant', errorMsg);
      speak(errorMsg);
    }
  };

  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not supported in your browser');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      setTranscript('');
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const handleTextSubmit = () => {
    if (textInput.trim()) {
      handleCommand(textInput);
      setTextInput('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') handleTextSubmit();
  };

  const QuickAction = ({ icon: Icon, label, command }) => (
    <button
      onClick={() => handleCommand(command)}
      className="flex flex-col items-center justify-center p-4 bg-white rounded-xl shadow-md hover:shadow-lg transition-all hover:scale-105"
    >
      <Icon className="w-8 h-8 mb-2 text-blue-600" />
      <span className="text-sm font-medium text-gray-700">{label}</span>
    </button>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-800 text-center mb-2">
            Elderly Care Assistant
          </h1>
          <p className="text-gray-600 text-center">Your friendly voice companion</p>

          {/* ✅ Start Assistant Button added here */}
          {!assistantStarted && (
            <div className="text-center mt-6">
              <button
                onClick={() => {
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

        {/* Rest of your layout only shows after assistant starts */}
        {assistantStarted && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
                <h2 className="text-xl font-semibold text-gray-800 mb-4">Quick Actions</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <QuickAction icon={Clock} label="Time" command="what time is it" />
                  <QuickAction icon={Heart} label="Weather" command="what's the weather" />
                  <QuickAction icon={Bell} label="Reminders" command="list reminders" />
                  <QuickAction icon={Phone} label="Emergency" command="emergency help" />
                </div>
              </div>

              <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
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
                        <p className="text-base">{msg.content}</p>
                        <span className="text-xs opacity-70 mt-1 block">
                          {msg.timestamp.toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>

                <div className="flex items-center gap-4">
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

            <div className="space-y-6">
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
