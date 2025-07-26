import React, { useState, useEffect } from 'react';
import './App.css';
import { apiService } from './api/apiService';

function App() {
  const [selectedAgents, setSelectedAgents] = useState([]);
  const [scenario, setScenario] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [apiUrl, setApiUrl] = useState(''); // Dynamic API URL from config

  // Haal agents op van backend API
  useEffect(() => {
    const fetchAgents = async () => {
      console.log('🚀 Starting fetchAgents...');
      
      try {
        // Haal eerst config op om API URL te krijgen
        console.log('📡 Fetching config from /config...');
        const configResponse = await fetch('/config');
        console.log('⚙️ Config response status:', configResponse.status, configResponse.statusText);
        
        if (!configResponse.ok) {
          throw new Error(`Config fetch failed: ${configResponse.status} ${configResponse.statusText}`);
        }
        
        const config = await configResponse.json();
        console.log('⚙️ Frontend config loaded:', config);
        
        // Set the API URL in state for use throughout the component
        // Fallback to working backend URL if config API_URL is invalid
        let apiUrl = config.API_URL;
        if (!apiUrl || apiUrl.includes('localhost:8000')) {
          apiUrl = 'https://backend-aiagents-gov.victoriouscoast-531c9ceb.westeurope.azurecontainerapps.io/api';
          console.log('🔄 Using fallback API URL:', apiUrl);
        }
        setApiUrl(apiUrl);
        
        const agentToolsUrl = `${config.API_URL}/agent-tools`;
        console.log('🎯 Fetching agents from:', agentToolsUrl);
        
        // Test direct fetch with detailed logging
        const response = await fetch(agentToolsUrl, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          },
          credentials: 'omit' // Explicitly no credentials
        });
        
        console.log('📡 Backend response received:', {
          status: response.status,
          statusText: response.statusText,
          url: response.url,
          headers: Object.fromEntries(response.headers.entries())
        });
        
        if (!response.ok) {
          throw new Error(`Backend API error: ${response.status} ${response.statusText} at ${agentToolsUrl}`);
        }
        
        const data = await response.json();
        console.log('📊 Backend data received:', data);
        console.log('📊 Data type:', typeof data, 'Array?', Array.isArray(data));
        
        if (!Array.isArray(data)) {
          throw new Error('Expected array from backend, got: ' + typeof data);
        }
        
        const formattedAgents = data.map((agent: any, index: number) => ({
          id: index + 1,
          name: agent.agent,
          description: agent.description,
          expertise: agent.agent
        }));
        
        console.log('✅ Formatted agents:', formattedAgents);
        setAgents(formattedAgents);
        setLoading(false);
      } catch (error: any) {
        console.error('❌ Error in fetchAgents:', error);
        console.error('❌ Error name:', error.name);
        console.error('❌ Error message:', error.message);
        console.error('❌ Error stack:', error.stack);
        setLoading(false);
      }
    };

    fetchAgents();
  }, []);

  const toggleAgent = (agent) => {
    setSelectedAgents(prev => {
      const isSelected = prev.some(a => a.id === agent.id);
      if (isSelected) {
        return prev.filter(a => a.id !== agent.id);
      } else {
        return [...prev, agent];
      }
    });
  };

  const analyzeScenario = async () => {
    if (selectedAgents.length === 0 || !scenario.trim()) {
      alert('Selecteer minimaal één agent en voer een scenario in');
      return;
    }

    if (!apiUrl) {
      alert('API URL niet beschikbaar. Probeer de pagina te verversen.');
      return;
    }

    setIsAnalyzing(true);
    
    try {
      const response = await apiService.submitInputTask({
        session_id: `session_${Date.now()}`,
        description: scenario
      });
      
      setAnalysis({
        agent_responses: selectedAgents.map(agent => ({
          agent_name: agent.name,
          agent_expertise: agent.expertise,
          response: `Echte AI analyse van ${agent.name}:\n\n${JSON.stringify(response, null, 2)}`
        }))
      });

      if (response.ok) {
        const result = await response.json();
        console.log('🎯 Backend response:', result);
        
        // Handle different response formats from backend
        let analysisResult;
        
        if (result.agent_responses) {
          // New format: backend returns proper agent_responses
          analysisResult = result;
        } else if (result.detail && result.detail.includes('Resource not found')) {
          // Backend configuration issue - create mock responses for selected agents
          analysisResult = {
            agent_responses: selectedAgents.map(agent => ({
              agent_name: agent.name,
              agent_expertise: agent.expertise,
              response: `AI Analyse van ${agent.name} voor: "${scenario}"\n\n` +
                       `Als ${agent.expertise} specialist zie ik de volgende aspecten:\n\n` +
                       `• Strategische overwegingen voor dit scenario\n` +
                       `• Impact op verschillende stakeholders\n` +
                       `• Aanbevolen vervolgstappen\n` +
                       `• Risico's en kansen\n\n` +
                       `Let op: Dit is een tijdelijke respons terwijl de backend configuratie wordt bijgewerkt.`
            }))
          };
        } else {
          // Other response format - create response based on result
          analysisResult = {
            agent_responses: selectedAgents.map(agent => ({
              agent_name: agent.name,
              agent_expertise: agent.expertise,
              response: `Response van ${agent.name}:\n\n${JSON.stringify(result, null, 2)}`
            }))
          };
        }
        
        setAnalysis(analysisResult);
      } else {
        alert('Fout: ' + response.status);
      }
    } catch (error: any) {
      console.error('❌ Backend call failed:', error);
      
      // Create fallback response when backend is completely unavailable
      setAnalysis({
        agent_responses: selectedAgents.map(agent => ({
          agent_name: agent.name,
          agent_expertise: agent.expertise,
          response: `Fallback analyse van ${agent.name}:\n\n` +
                   `Scenario: "${scenario}"\n\n` +
                   `Als ${agent.expertise} expert zou ik het volgende analyseren:\n\n` +
                   `• Identificatie van kernuitdagingen\n` +
                   `• Stakeholder impact assessment\n` +
                   `• Strategische aanbevelingen\n` +
                   `• Implementation roadmap\n\n` +
                   `Deze analyse is gegenereerd in offline modus. ` +
                   `Voor volledige AI-powered analysis, controleer de backend verbinding.`
        }))
      });
      
      alert('Backend tijdelijk niet bereikbaar. Fallback analyse getoond.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #f3e8ff 0%, #fce7f3 50%, #e0e7ff 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}>
        <div style={{
          background: 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(20px)',
          borderRadius: '24px',
          padding: '48px',
          textAlign: 'center'
        }}>
          <div style={{
            width: '40px',
            height: '40px',
            border: '4px solid #8b5cf6',
            borderTop: '4px solid transparent',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 24px'
          }}></div>
          <h2 style={{ color: '#8b5cf6', margin: 0 }}>Laden van agents uit CMS...</h2>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f3e8ff 0%, #fce7f3 50%, #e0e7ff 100%)',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <header style={{
        background: 'rgba(255, 255, 255, 0.9)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(168, 85, 247, 0.2)',
        position: 'sticky',
        top: 0,
        zIndex: 50
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          padding: '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              padding: '8px',
              background: 'linear-gradient(135deg, #8b5cf6, #ec4899)',
              borderRadius: '12px',
              boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
            }}>
              <span style={{ fontSize: '24px' }}>✨</span>
            </div>
            <div>
              <h1 style={{
                fontSize: '24px',
                fontWeight: 'bold',
                background: 'linear-gradient(135deg, #8b5cf6, #ec4899)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                margin: 0
              }}>
                SoMC.AI
              </h1>
              <p style={{ fontSize: '14px', color: '#6b7280', margin: 0 }}>
                The AI-powered government platform
              </p>
            </div>
          </div>
          <div style={{ fontSize: '14px', color: '#8b5cf6', fontWeight: '500' }}>
            CMS-Powered ✨
          </div>
        </div>
      </header>

      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '48px 20px' }}>
        
        <div style={{ textAlign: 'center', marginBottom: '48px' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 24px',
            background: 'rgba(255, 255, 255, 0.8)',
            backdropFilter: 'blur(10px)',
            borderRadius: '50px',
            border: '1px solid rgba(168, 85, 247, 0.2)',
            color: '#8b5cf6',
            fontSize: '14px',
            fontWeight: '500',
            marginBottom: '24px'
          }}>
            ⚡ Powered by Dynamic CMS Agents
          </div>
          <h2 style={{
            fontSize: '56px',
            fontWeight: 'bold',
            background: 'linear-gradient(135deg, #1f2937, #8b5cf6, #ec4899)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            lineHeight: '1.1',
            margin: '0 0 24px 0'
          }}>
            AI-Gestuurde<br />Beleidsanalyse
          </h2>
          <p style={{
            fontSize: '20px',
            color: '#374151',
            maxWidth: '800px',
            margin: '0 auto',
            lineHeight: '1.6'
          }}>
            Agents worden dynamisch geladen uit het CMS. Voeg nieuwe agents toe via Directus!
          </p>
        </div>

        <div style={{ marginBottom: '48px' }}>
          <div style={{ textAlign: 'center', marginBottom: '32px' }}>
            <h3 style={{ fontSize: '32px', fontWeight: 'bold', color: '#1f2937', margin: '0 0 12px 0' }}>
              Selecteer AI Specialisten
            </h3>
            <p style={{ fontSize: '18px', color: '#6b7280', margin: 0 }}>
              {agents.length} agents geladen uit CMS
            </p>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '24px',
            marginBottom: '32px'
          }}>
            {agents.map((agent) => (
              <div
                key={agent.id}
                onClick={() => toggleAgent(agent)}
                style={{
                  padding: '32px',
                  borderRadius: '24px',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  background: selectedAgents.some(a => a.id === agent.id)
                    ? 'linear-gradient(135deg, rgba(168, 85, 247, 0.1), rgba(236, 72, 153, 0.1))'
                    : 'rgba(255, 255, 255, 0.8)',
                  backdropFilter: 'blur(20px)',
                  border: selectedAgents.some(a => a.id === agent.id)
                    ? '2px solid #8b5cf6'
                    : '1px solid rgba(209, 213, 219, 0.3)',
                  boxShadow: selectedAgents.some(a => a.id === agent.id)
                    ? '0 20px 40px rgba(168, 85, 247, 0.2)'
                    : '0 4px 12px rgba(0, 0, 0, 0.05)',
                  position: 'relative'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
                  <div style={{
                    padding: '16px',
                    borderRadius: '16px',
                    background: selectedAgents.some(a => a.id === agent.id)
                      ? 'linear-gradient(135deg, #8b5cf6, #ec4899)'
                      : 'rgba(168, 85, 247, 0.1)',
                    color: selectedAgents.some(a => a.id === agent.id) ? 'white' : '#8b5cf6'
                  }}>
                    <span style={{ fontSize: '24px' }}>
                      {agent.expertise === 'demografie' ? '👥' : agent.expertise === 'economie' ? '📈' : '🏠'}
                    </span>
                  </div>
                  <div>
                    <h4 style={{ fontSize: '18px', fontWeight: 'bold', color: '#1f2937', margin: '0 0 8px 0' }}>
                      {agent.name}
                    </h4>
                    <span style={{
                      color: '#8b5cf6',
                      fontWeight: '500',
                      textTransform: 'capitalize',
                      padding: '4px 12px',
                      background: 'rgba(168, 85, 247, 0.1)',
                      borderRadius: '20px',
                      fontSize: '14px'
                    }}>
                      {agent.expertise}
                    </span>
                  </div>
                </div>
                <p style={{ color: '#6b7280', lineHeight: '1.5', margin: 0 }}>
                  {agent.description}
                </p>
                
                {selectedAgents.some(a => a.id === agent.id) && (
                  <div style={{
                    position: 'absolute',
                    top: '24px',
                    right: '24px',
                    padding: '8px',
                    background: 'linear-gradient(135deg, #10b981, #059669)',
                    borderRadius: '50%',
                    boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)'
                  }}>
                    <span style={{ color: 'white', fontSize: '16px', fontWeight: 'bold' }}>✓</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div style={{
          background: 'rgba(255, 255, 255, 0.8)',
          backdropFilter: 'blur(20px)',
          borderRadius: '24px',
          padding: '32px',
          border: '1px solid rgba(209, 213, 219, 0.3)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08)',
          marginBottom: '48px'
        }}>
          <h3 style={{
            fontSize: '32px',
            fontWeight: 'bold',
            color: '#1f2937',
            marginBottom: '32px',
            textAlign: 'center'
          }}>
            Scenario Beschrijving
          </h3>
          
          <textarea
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            placeholder="Beschrijf uw beleidsscenario hier..."
            style={{
              width: '100%',
              height: '160px',
              padding: '24px',
              background: 'rgba(255, 255, 255, 0.7)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(209, 213, 219, 0.5)',
              borderRadius: '16px',
              fontSize: '16px',
              lineHeight: '1.5',
              resize: 'none',
              outline: 'none',
              boxSizing: 'border-box',
              marginBottom: '24px'
            }}
          />
          
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 16px',
              background: 'rgba(168, 85, 247, 0.1)',
              borderRadius: '50px',
              border: '1px solid rgba(168, 85, 247, 0.2)'
            }}>
              <span style={{ color: '#374151', fontSize: '14px', fontWeight: '500' }}>
                {selectedAgents.length} van {agents.length} agents geselecteerd
              </span>
            </div>
            
            <button
              onClick={analyzeScenario}
              disabled={isAnalyzing || selectedAgents.length === 0 || !scenario.trim()}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '16px 32px',
                background: isAnalyzing || selectedAgents.length === 0 || !scenario.trim()
                  ? '#9ca3af'
                  : 'linear-gradient(135deg, #8b5cf6, #ec4899)',
                color: 'white',
                borderRadius: '16px',
                border: 'none',
                cursor: isAnalyzing || selectedAgents.length === 0 || !scenario.trim() ? 'not-allowed' : 'pointer',
                fontSize: '16px',
                fontWeight: '600',
                boxShadow: '0 8px 24px rgba(139, 92, 246, 0.3)',
                transition: 'all 0.3s ease'
              }}
            >
              {isAnalyzing ? (
                <>
                  <div style={{
                    width: '20px',
                    height: '20px',
                    border: '2px solid white',
                    borderTop: '2px solid transparent',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }}></div>
                  Analyseren...
                </>
              ) : (
                <>
                  <span style={{ fontSize: '20px' }}>📤</span>
                  Start Analyse
                </>
              )}
            </button>
          </div>
        </div>

        {analysis && (
          <div style={{
            background: 'rgba(255, 255, 255, 0.8)',
            backdropFilter: 'blur(20px)',
            borderRadius: '24px',
            padding: '32px',
            border: '1px solid rgba(209, 213, 219, 0.3)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08)'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              marginBottom: '32px'
            }}>
              <div style={{
                padding: '12px',
                background: 'linear-gradient(135deg, #10b981, #059669)',
                borderRadius: '16px',
                boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)'
              }}>
                <span style={{ color: 'white', fontSize: '24px' }}>✨</span>
              </div>
              <h3 style={{
                fontSize: '32px',
                fontWeight: 'bold',
                color: '#1f2937',
                margin: 0
              }}>
                Analyse Resultaat
              </h3>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
              {analysis.agent_responses.map((response, index) => (
                <div key={index} style={{
                  padding: '24px',
                  background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.05), rgba(236, 72, 153, 0.05))',
                  borderRadius: '16px',
                  borderLeft: '4px solid #8b5cf6'
                }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '16px',
                    marginBottom: '16px'
                  }}>
                    <div style={{
                      padding: '12px',
                      background: 'linear-gradient(135deg, #8b5cf6, #ec4899)',
                      borderRadius: '12px',
                      boxShadow: '0 4px 12px rgba(139, 92, 246, 0.3)'
                    }}>
                      <span style={{ color: 'white', fontSize: '24px' }}>
                        {response.agent_expertise === 'demografie' ? '👥' : response.agent_expertise === 'economie' ? '📈' : '🏠'}
                      </span>
                    </div>
                    <h4 style={{
                      fontSize: '20px',
                      fontWeight: 'bold',
                      color: '#1f2937',
                      margin: 0
                    }}>
                      {response.agent_name}
                    </h4>
                  </div>
                  <pre style={{ color: '#374151', lineHeight: '1.6', whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
                    {response.response}
                  </pre>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default App;
