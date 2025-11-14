import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { ThemeProvider } from "./components/ThemeProvider";
import Index from "./pages/Index";
import Auth from "./pages/Auth";
import Dashboard from "./pages/Dashboard";
import FileIntegrity from "./pages/FileIntegrity";
import NetworkMonitoring from "./pages/NetworkMonitoring";
import AIAnomaly from "./pages/AIAnomaly";
import IncidentManagement from "./pages/IncidentManagement";

import EmployeeManagement from "./pages/EmployeeManagement";
import SystemConfig from "./pages/SystemConfig";
import Reports from "./pages/Reports";
import AuditLogs from "./pages/AuditLogs";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }
  
  return isAuthenticated ? <>{children}</> : <Navigate to="/auth" replace />;
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider defaultTheme="light" storageKey="intellifim-ui-theme">
      <AuthProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Index />} />
              <Route path="/auth" element={<Auth />} />
              <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
              <Route path="/file-integrity" element={<ProtectedRoute><FileIntegrity /></ProtectedRoute>} />
              <Route path="/network-monitoring" element={<ProtectedRoute><NetworkMonitoring /></ProtectedRoute>} />
              <Route path="/ai-anomaly" element={<ProtectedRoute><AIAnomaly /></ProtectedRoute>} />
              <Route path="/incidents" element={<ProtectedRoute><IncidentManagement /></ProtectedRoute>} />

              <Route path="/employees" element={<ProtectedRoute><EmployeeManagement /></ProtectedRoute>} />
              <Route path="/config" element={<ProtectedRoute><SystemConfig /></ProtectedRoute>} />
              <Route path="/reports" element={<ProtectedRoute><Reports /></ProtectedRoute>} />
              <Route path="/logs" element={<ProtectedRoute><AuditLogs /></ProtectedRoute>} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </TooltipProvider>
      </AuthProvider>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;
