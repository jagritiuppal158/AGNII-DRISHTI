import React, { useState, useMemo, useEffect } from 'react';
import MapView from './components/Map';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { fetchLocations, fetchLocationById, getDataSourceStatus, DATA_SOURCE_MODE } from './data/dataSource';
import { classLabels, statusLabels, statusOptions, classOptions, getClassBadgeClass, getStatusBadgeClass } from './data/constants';

function App() {
  const [selectedClass, setSelectedClass] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [selectedLocationId, setSelectedLocationId] = useState(null);
  const [locations, setLocations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Load locations on mount
  useEffect(() => {
    let mounted = true;
    async function loadLocations() {
      setIsLoading(true);
      try {
        const data = await fetchLocations();
        if (mounted) {
          setLocations(data);
        }
      } catch (error) {
        console.error('Failed to load locations:', error);
      } finally {
        if (mounted) setIsLoading(false);
      }
    }
    loadLocations();
    return () => { mounted = false; };
  }, []);

  const dataSourceStatus = getDataSourceStatus();

  const filteredLocations = useMemo(() => {
    return locations.filter(loc => {
      const classMatch = !selectedClass || loc.current_class === selectedClass;
      const statusMatch = !selectedStatus || loc.status === selectedStatus;
      return classMatch && statusMatch;
    });
  }, [locations, selectedClass, selectedStatus]);

  // Clear selection if the selected location is no longer in filtered results
  useEffect(() => {
    if (selectedLocationId && !filteredLocations.some(l => l.id === selectedLocationId)) {
      setSelectedLocationId(null);
    }
  }, [filteredLocations, selectedLocationId]);

  const stats = useMemo(() => {
    // Stats use the data source locations (currently mock)
    // Will be replaced with GET /v1/locations during real API integration (Step 8).
    // High Priority uses top 20% by priority_score as temporary fallback until backend provides real threshold.
    const TOP_PERCENTILE = 0.2;
    const count = locations.length;
    const topN = Math.max(1, Math.ceil(count * TOP_PERCENTILE));
    const topPriorityIds = [...locations]
      .sort((a, b) => b.priority_score - a.priority_score)
      .slice(0, topN)
      .map(l => l.id);
    const isHighPriority = (loc) => topPriorityIds.includes(loc.id);

    return {
      activeLocations: locations.length,
      highPriority: locations.filter(isHighPriority).length,
      industrialSuspected: locations.filter(l => l.current_class === 'industrial_fire').length,
      recurringSites: locations.filter(l => l.status === 'recurring' || l.status === 'persistent').length,
    };
  }, [locations]);

  const handleLocationSelect = (locationId) => {
    setSelectedLocationId(prev => prev === locationId ? null : locationId);
  };

  const selectedLocation = locations.find(l => l.id === selectedLocationId);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <header className="top-bar sticky top-0 z-50">
        <div className="max-w-full mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
              <svg className="w-6 h-6 text-slate-950" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-100">AGNI-DRISHTI</h1>
          </div>
          <div className="flex items-center gap-3">
            <span className={`badge-live ${dataSourceStatus.status === 'live' ? '' : 'bg-amber-500/20 text-amber-400 border-amber-500/30'}`} id="data-status-badge">
              <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${dataSourceStatus.status === 'live' ? 'bg-green-500 animate-pulse' : 'bg-amber-500'}`}></span>
              {dataSourceStatus.label}
            </span>
          </div>
        </div>
      </header>

      <main className="flex-1 p-6 overflow-hidden">
        {isLoading ? (
          <div className="flex-1 flex items-center justify-center text-slate-400">
            <svg className="animate-spin h-8 w-8 text-amber-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
        ) : (
          <div className="max-w-full mx-auto h-full flex flex-col">
            <div className="flex flex-col sm:flex-row gap-4 mb-4 p-4 bg-slate-900 border border-slate-700 rounded-xl">
              <div className="flex-1 sm:w-64">
                <label className="block text-xs font-medium text-slate-400 mb-1">Class</label>
                <select
                  value={selectedClass}
                  onChange={(e) => setSelectedClass(e.target.value)}
                  className="filter-select w-full"
                >
                  {classOptions.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
              <div className="flex-1 sm:w-64">
                <label className="block text-xs font-medium text-slate-400 mb-1">Status</label>
                <select
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  className="filter-select w-full"
                >
                  {statusOptions.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
              <div className="flex items-end sm:w-32">
                <span className="text-sm text-slate-400">{filteredLocations.length} locations</span>
              </div>
            </div>

            <div className="flex-1 flex gap-6 min-h-0">
              <section className="flex-1 min-w-0 card flex flex-col min-h-0">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-slate-100">Map View</h2>
                  <div className="flex items-center gap-2 text-sm text-slate-400">
                    <span>{filteredLocations.length} markers</span>
                  </div>
                </div>
                <div className="flex-1 bg-slate-950 rounded-lg border border-slate-800 relative overflow-hidden min-h-0">
                  <MapView
                    locations={filteredLocations}
                    selectedLocationId={selectedLocationId}
                    onLocationClick={handleLocationSelect}
                  />
                </div>
              </section>

              <aside className="w-full lg:w-96 flex-shrink-0 flex flex-col gap-6 min-h-0">
                <div className="grid grid-cols-2 gap-3">
                  <div className="stat-card">
                    <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">Active Locations</p>
                    <p className="text-3xl font-bold text-slate-100">{stats.activeLocations}</p>
                  </div>
                  <div className="stat-card">
                    <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">High Priority</p>
                    <p className="text-3xl font-bold text-red-400">{stats.highPriority}</p>
                  </div>
                  <div className="stat-card">
                    <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">Industrial Suspected</p>
                    <p className="text-3xl font-bold text-amber-400">{stats.industrialSuspected}</p>
                  </div>
                  <div className="stat-card">
                    <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">Recurring Sites</p>
                    <p className="text-3xl font-bold text-purple-400">{stats.recurringSites}</p>
                  </div>
                </div>

                <div className="flex-1 min-h-0 card flex flex-col">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-slate-100">Detected Locations</h2>
                    <span className="text-xs text-slate-400">{filteredLocations.length} results</span>
                  </div>
                  <div className="flex-1 overflow-y-auto space-y-2 pr-1" style={{ maxHeight: 'calc(100vh - 300px)' }}>
                    {filteredLocations.map(loc => (
                      <div
                        key={loc.id}
                        className={`location-item ${selectedLocationId === loc.id ? 'location-item-selected' : ''}`}
                        onClick={() => handleLocationSelect(loc.id)}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-sm text-slate-100 truncate">{loc.name}</p>
                            <p className="text-xs text-slate-500 mt-0.5">{loc.region} • {loc.latitude.toFixed(4)}, {loc.longitude.toFixed(4)}</p>
                          </div>
                          <div className="flex flex-col items-end gap-1 flex-shrink-0">
                            {loc.current_class ? (
                              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getClassBadgeClass(loc.current_class)}`}>
                                {classLabels[loc.current_class]}
                              </span>
                            ) : (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border bg-amber-500/20 text-amber-400 border-amber-500/30">
                                Pending
                              </span>
                            )}
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getStatusBadgeClass(loc.status)}`}>
                              {statusLabels[loc.status]}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                    {filteredLocations.length === 0 && (
                      <div className="text-center py-8 text-slate-500">
                        <svg className="w-12 h-12 mx-auto mb-3 text-slate-700" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <p>No locations match the current filters</p>
                      </div>
                    )}
                  </div>
                </div>

                {selectedLocation && (
                  <div className="card border-amber-500/50 bg-slate-900/80">
                    <h2 className="text-lg font-semibold text-slate-100 mb-4 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                      Selected Location Details
                    </h2>
                    <div className="space-y-3 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Name</span>
                        <span className="font-medium text-slate-100">{selectedLocation.name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Classification</span>
                        {selectedLocation.current_class && selectedLocation.current_confidence ? (
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getClassBadgeClass(selectedLocation.current_class)}`}>
                            {classLabels[selectedLocation.current_class]}
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border bg-amber-500/20 text-amber-400 border-amber-500/30">
                            Pending classification
                          </span>
                        )}
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Status</span>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getStatusBadgeClass(selectedLocation.status)}`}>
                          {statusLabels[selectedLocation.status]}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Confidence</span>
                        {selectedLocation.current_confidence ? (
                          <span className="text-slate-100">{(selectedLocation.current_confidence * 100).toFixed(0)}%</span>
                        ) : (
                          <span className="text-slate-500">—</span>
                        )}
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Detection Count</span>
                        <span className="text-slate-100">{selectedLocation.detection_count}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Priority Score</span>
                        <span className="text-amber-400 font-medium">{(selectedLocation.priority_score * 100).toFixed(0)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Region</span>
                        <span className="text-slate-100">{selectedLocation.region}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Coordinates</span>
                        <span className="text-slate-100 font-mono text-xs">{selectedLocation.latitude.toFixed(4)}, {selectedLocation.longitude.toFixed(4)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">First Detected</span>
                        <span className="text-slate-100 text-xs">{new Date(selectedLocation.first_detected_at).toLocaleDateString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Last Detected</span>
                        <span className="text-slate-100 text-xs">{new Date(selectedLocation.last_detected_at).toLocaleDateString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Nearest Infrastructure</span>
                        <span className="text-slate-100">{selectedLocation.infrastructure_type}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Infrastructure Distance</span>
                        <span className="text-slate-100">{selectedLocation.infrastructure_distance} km</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Land Cover Class</span>
                        <span className="text-slate-100">{selectedLocation.land_cover_class}</span>
                      </div>
                      {selectedLocation.detection_history && selectedLocation.detection_history.length > 0 && (
                        <div className="pt-4 border-t border-slate-700">
                          <h3 className="text-sm font-semibold text-slate-100 mb-3">Detection History</h3>
                          <div style={{ height: 180 }}>
                            <ResponsiveContainer width="100%" height="100%">
                              <LineChart
                                data={selectedLocation.detection_history}
                                margin={{ top: 5, right: 5, left: 0, bottom: 0 }}
                              >
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                                <XAxis
                                  dataKey="date"
                                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                                  axisLine={{ stroke: '#334155' }}
                                  tickLine={false}
                                />
                                <YAxis
                                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                                  axisLine={{ stroke: '#334155' }}
                                  tickLine={false}
                                />
                                <Tooltip
                                  contentStyle={{
                                    backgroundColor: '#0f172a',
                                    border: '1px solid #334155',
                                    borderRadius: '0.5rem',
                                    color: '#e2e8f0',
                                  }}
                                  labelFormatter={(date) => new Date(date).toLocaleDateString()}
                                  formatter={(value) => [value, 'detections']}
                                />
                                <Line
                                  type="monotone"
                                  dataKey="count"
                                  stroke="#f59e0b"
                                  strokeWidth={2}
                                  dot={{ fill: '#f59e0b', strokeWidth: 2, r: 4 }}
                                  activeDot={{ r: 6, fill: '#f59e0b' }}
                                />
                              </LineChart>
                            </ResponsiveContainer>
                          </div>
                        </div>
                      )}
                      {selectedLocation.open_case_id && (
                        <div className="flex justify-between pt-2 border-t border-slate-700">
                          <span className="text-slate-400">Open Case</span>
                          <span className="text-amber-400 font-mono text-xs">{selectedLocation.open_case_id}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </aside>
            </div>
          </div>
        )}
      </main>

      <footer className="border-t border-slate-800 bg-slate-900/50 py-4 px-6">
        <div className="max-w-full mx-auto flex items-center justify-between text-sm text-slate-500">
          <span>AGNI-DRISHTI — GIS Monitoring Dashboard</span>
          <span>v0.1.0 • Data: {dataSourceStatus.label}</span>
        </div>
      </footer>
    </div>
  )
}

export default App