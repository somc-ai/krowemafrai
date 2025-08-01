'use client';

import React, { useState } from 'react';

function SoMCDashboard() {
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
    
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const demoResponse = {
      agent_responses: selectedAgents.map(agent => ({
        agent_name: agent.name,
        agent_expertise: agent.expertise,
        response: `Demo analyse van ${agent.name}: ${scenario.slice(0, 50)}...

Dit is een voorbeeldanalyse die laat zien hoe ${agent.expertise} factoren een rol spelen in uw scenario.

Belangrijke overwegingen:
- Impact op lokale gemeenschap
- Economische effecten op lange termijn  
- Beleidsaanbevelingen voor implementatie`
      }))
    };
    
    setAnalysis(demoResponse);
    setIsAnalyzing(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-indigo-50 relative overflow-hidden">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-r from-purple-200 to-pink-200 rounded-full mix-blend-multiply filter blur-xl opacity-40 animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-r from-indigo-200 to-purple-200 rounded-full mix-blend-multiply filter blur-xl opacity-40 animate-pulse delay-1000"></div>
      </div>

      <header className="relative bg-white/70 backdrop-blur-xl border-b border-purple-100 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl shadow-lg">
                <div className="w-6 h-6 text-white flex items-center justify-center font-bold">✨</div>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                  SoMC.AI
                </h1>
                <p className="text-sm text-gray-600">The AI-powered government platform</p>
              </div>
            </div>
            <div className="text-sm text-purple-700 font-medium">Demo Modus</div>
          </div>
        </div>
      </header>

      <div className="relative max-w-7xl mx-auto px-6 py-12 space-y-12">
        <div className="text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-6 py-3 bg-white/80 backdrop-blur-sm rounded-full border border-purple-200 text-purple-700 text-sm font-medium shadow-sm">
            ⚡ Powered by Advanced AI Agents
          </div>
          <h2 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-gray-900 via-purple-800 to-pink-800 bg-clip-text text-transparent leading-tight">
            AI-Gestuurde
            <br />
            Beleidsanalyse
          </h2>
          <p className="text-xl text-gray-700 max-w-3xl mx-auto leading-relaxed">
            Ontdek de kracht van gespecialiseerde AI-agents voor demografische, economische en woningbouwanalyses. 
            Maak weloverwogen beleidsbeslissingen met realtime insights.
          </p>
        </div>

        <section className="space-y-8">
          <div className="text-center space-y-3">
            <h3 className="text-3xl font-bold text-gray-900">
              Selecteer AI Specialisten
            </h3>
            <p className="text-gray-600 text-lg">
              Kies de experts die relevant zijn voor uw scenario analyse
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {agents.map((agent, index) => (
              <div
                key={agent.id}
                onClick={() => toggleAgent(agent)}
                className={`group relative p-8 rounded-3xl cursor-pointer transition-all duration-300 hover:scale-105 ${
                  selectedAgents.some(a => a.id === agent.id)
                    ? 'bg-gradient-to-br from-purple-100 to-pink-100 border-2 border-purple-300 shadow-xl shadow-purple-200/50'
                    : 'bg-white/80 backdrop-blur-sm border border-gray-200 hover:bg-white hover:border-purple-200 hover:shadow-lg'
                }`}
              >
                <div className="relative">
                  <div className="flex items-center gap-4 mb-6">
                    <div className={`p-4 rounded-2xl transition-all duration-300 ${
                      selectedAgents.some(a => a.id === agent.id)
                        ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg'
                        : 'bg-purple-50 text-purple-600 group-hover:bg-purple-100'
                    }`}>
                      <div className="w-6 h-6 flex items-center justify-center font-bold">
                        {agent.expertise === 'demografie' ? '👥' : agent.expertise === 'economie' ? '📈' : '🏠'}
                      </div>
                    </div>
                    <div>
                      <h4 className="font-bold text-gray-900 text-lg">{agent.name}</h4>
                      <span className="text-purple-600 font-medium capitalize px-3 py-1 bg-purple-100 rounded-full text-sm">
                        {agent.expertise}
                      </span>
                    </div>
                  </div>
                  <p className="text-gray-600 leading-relaxed">
                    {agent.description}
                  </p>
                  
                  {selectedAgents.some(a => a.id === agent.id) && (
                    <div className="absolute top-6 right-6 p-2 bg-gradient-to-r from-green-400 to-emerald-400 rounded-full shadow-lg">
                      <div className="w-5 h-5 text-white flex items-center justify-center font-bold">✓</div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="space-y-8">
          <div className="bg-white/80 backdrop-blur-xl rounded-3xl p-8 border border-gray-200 shadow-lg">
            <h3 className="text-3xl font-bold text-gray-900 mb-8 text-center">
              Scenario Beschrijving
            </h3>
            <div className="space-y-6">
              <textarea
                value={scenario}
                onChange={(e) => setScenario(e.target.value)}
                placeholder="Beschrijf uw beleidsscenario hier... Bijvoorbeeld: 'Wat zijn de effecten van het bouwen van 500 nieuwe woningen in de gemeente op demografie, economie en infrastructuur?'"
                className="w-full h-40 p-6 bg-white/70 backdrop-blur-sm border border-gray-300 rounded-2xl text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent resize-none text-lg leading-relaxed"
              />
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 px-4 py-2 bg-purple-50 rounded-full border border-purple-200">
                  <span className="text-gray-700 text-sm font-medium">
                    {selectedAgents.length} van {agents.length} agents geselecteerd
                  </span>
                </div>
                
                <button
                  onClick={analyzeScenario}
                  disabled={isAnalyzing || selectedAgents.length === 0 || !scenario.trim()}
                  className="flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-2xl hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 hover:scale-105 hover:shadow-xl font-semibold text-lg"
                >
                  {isAnalyzing ? (
                    <>
                      <div className="w-5 h-5 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                      Analyseren...
                    </>
                  ) : (
                    <>
                      <div className="w-5 h-5">📤</div>
                      Start Analyse
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </section>

        {analysis && (
          <section className="space-y-8">
            <div className="bg-white/80 backdrop-blur-xl rounded-3xl p-8 border border-gray-200 shadow-lg">
              <div className="flex items-center gap-3 mb-8">
                <div className="p-3 bg-gradient-to-r from-green-500 to-emerald-500 rounded-2xl shadow-lg">
                  <div className="w-6 h-6 text-white flex items-center justify-center font-bold">✨</div>
                </div>
                <h3 className="text-3xl font-bold text-gray-900">
                  Analyse Resultaat
                </h3>
              </div>
              
              <div className="space-y-8">
                {analysis.agent_responses.map((response, index) => (
                  <div key={index} className="p-6 bg-gradient-to-r from-purple-50 to-pink-50 rounded-2xl border-l-4 border-purple-400">
                    <div className="flex items-center gap-4 mb-4">
                      <div className="p-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl shadow-lg">
                        <div className="w-6 h-6 text-white flex items-center justify-center font-bold">
                          {response.agent_expertise === 'demografie' ? '👥' : response.agent_expertise === 'economie' ? '📈' : '🏠'}
                        </div>
                      </div>
                      <h4 className="font-bold text-gray-900 text-xl">
                        {response.agent_name}
                      </h4>
                    </div>
                    <div className="prose prose-lg max-w-none">
                      {response.response.split('\n').map((paragraph, i) => (
                        paragraph.trim() && (
                          <p key={i} className="mb-4 text-gray-700 leading-relaxed">
                            {paragraph}
                          </p>
                        )
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}
      </div>

      <footer className="relative bg-white/70 backdrop-blur-xl border-t border-gray-200 mt-20">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="text-center text-gray-600">
            <p className="text-lg font-medium">© 2025 SoMC.AI - Government AI Analysis Platform</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default SoMCDashboard;