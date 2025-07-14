import React, { useState } from 'react';
import './App.css';

function App() {
  const [selectedAgents, setSelectedAgents] = useState([]);
  const [scenario, setScenario] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState(null);

  const agents = [
    {
      id: 1,
      name: "AI Demografie Zeeland",
      description: "Demografiespecialist voor bevolkingsanalyse en trends",
      expertise: "demografie"
    },
    {
      id: 2,
      name: "AI Economie Zeeland", 
      description: "Economiespecialist voor economische impact en groei",
      expertise: "economie"
    },
    {
      id: 3,
      name: "AI Wonen",
      description: "Woningbouwexpert voor huisvestingsbeleid en planning",
      expertise: "wonen"
    }
  ];

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

    setIsAnalyzing(true);
    
    try {
      const response = await fetch('http://127.0.0.1:8000/api/input_task', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task: scenario,
          agents: selectedAgents.map(agent => agent.expertise),
          session_id: `session_${Date.now()}`
        })
      });

      if (response.ok) {
        const result = await response.json();
        setAnalysis(result);
      } else {
        alert('Fout bij het uitvoeren van de analyse');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Verbindingsfout met de backend');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-3xl font-bold text-gray-900">SoMC.AI</h1>
              <span className="ml-2 text-sm text-gray-500">The AI-powered government platform</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="space-y-8">
          
          {/* Demo Modus Banner */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <span className="text-blue-600">⚡</span>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-blue-800">Demo Modus</h3>
                <p className="text-sm text-blue-700">Powered by Advanced AI Agents</p>
              </div>
            </div>
          </div>

          {/* AI-Gestuurde Beleidsanalyse */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">AI-Gestuurde Beleidsanalyse</h2>
            <p className="text-gray-600 mb-6">
              Ontdek de kracht van gespecialiseerde AI-agents voor demografische, economische en woningbouwanalyses. 
              Maak weloverwogen beleidsbeslissingen met realtime insights.
            </p>

            {/* Selecteer AI Specialisten */}
            <div className="mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Selecteer AI Specialisten</h3>
              <p className="text-sm text-gray-600 mb-4">Kies de experts die relevant zijn voor uw scenario analyse</p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {agents.map(agent => (
                  <div 
                    key={agent.id}
                    className={`border rounded-lg p-4 cursor-pointer transition-all ${
                      selectedAgents.some(a => a.id === agent.id)
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => toggleAgent(agent)}
                  >
                    <div className="flex items-start">
                      <div className="flex-shrink-0">
                        <div className={`w-4 h-4 rounded border-2 ${
                          selectedAgents.some(a => a.id === agent.id)
                            ? 'bg-blue-500 border-blue-500'
                            : 'border-gray-300'
                        }`}>
                          {selectedAgents.some(a => a.id === agent.id) && (
                            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                        </div>
                      </div>
                      <div className="ml-3">
                        <h4 className="font-medium text-gray-900">{agent.name}</h4>
                        <p className="text-sm text-gray-600 mt-1">{agent.description}</p>
                        <span className="inline-block mt-2 px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded">
                          {agent.expertise}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-4 text-sm text-gray-600">
                {selectedAgents.length} van {agents.length} agents geselecteerd
              </div>
            </div>

            {/* Scenario Beschrijving */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Scenario Beschrijving</h3>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                rows={4}
                placeholder="Beschrijf uw beleidsscenario..."
                value={scenario}
                onChange={(e) => setScenario(e.target.value)}
              />
            </div>

            {/* Start Analyse Button */}
            <button
              onClick={analyzeScenario}
              disabled={isAnalyzing || selectedAgents.length === 0 || !scenario.trim()}
              className={`w-full py-3 px-4 rounded-md font-medium ${
                isAnalyzing || selectedAgents.length === 0 || !scenario.trim()
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {isAnalyzing ? 'Analyseren...' : 'Start Analyse'}
            </button>
          </div>

          {/* Analysis Results */}
          {analysis && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Analyse Resultaten</h3>
              <div className="bg-gray-50 rounded-md p-4">
                <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                  {JSON.stringify(analysis, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-16">
        <div className="max-w-7xl
