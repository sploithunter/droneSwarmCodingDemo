import React from 'react';
import { WebSocketProvider } from './context/WebSocketContext';
import WebSocketContext from './context/WebSocketContext';
import useWebSocket from './hooks/useWebSocket';
import Header from './components/Header';
import MapPanel from './components/MapPanel';
import SwarmOverview from './components/SwarmOverview';
import AlertFeed from './components/AlertFeed';
import DroneSelector from './components/DroneSelector';
import TelemetryPanel from './components/TelemetryPanel';
import CommandPanel from './components/CommandPanel';

function Dashboard() {
  const { state, dispatch } = React.useContext(WebSocketContext);
  const wsRef = useWebSocket(dispatch);

  return (
    <div className="dashboard" data-testid="app">
      <Header />
      <div className="main-layout">
        <div className="left-panel">
          <MapPanel />
        </div>
        <div className="right-panel">
          <SwarmOverview />
          <AlertFeed />
        </div>
      </div>
      <DroneSelector />
      <div className="detail-layout">
        <div className="left-panel">
          <TelemetryPanel />
        </div>
        <div className="right-panel">
          <CommandPanel wsRef={wsRef} />
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <WebSocketProvider>
      <Dashboard />
    </WebSocketProvider>
  );
}
