export const mockDashboardStats = {
  totalFiles: 15847,
  anomaliesDetected: 23,
  activeIncidents: 5,
  systemHealth: 98.5,
};

export const mockFileIntegrity = [
  { id: '1', fileName: '/etc/passwd', hash: 'a3d5e...', status: 'unchanged', lastModified: '2025-10-19 08:30', changeType: '-' },
  { id: '2', fileName: '/var/www/config.php', hash: 'b7f2c...', status: 'modified', lastModified: '2025-10-19 10:15', changeType: 'content' },
  { id: '3', fileName: '/usr/bin/sudo', hash: 'c9e4a...', status: 'suspicious', lastModified: '2025-10-19 11:45', changeType: 'permissions' },
  { id: '4', fileName: '/home/admin/.ssh/authorized_keys', hash: 'd2b8f...', status: 'modified', lastModified: '2025-10-19 09:20', changeType: 'content' },
];

export const mockNetworkTraffic = [
  { id: '1', sourceIP: '192.168.1.105', destIP: '10.0.0.50', protocol: 'TCP', packetSize: 1420, anomalyScore: 0.85, timestamp: '2025-10-19 12:45:32' },
  { id: '2', sourceIP: '203.0.113.42', destIP: '192.168.1.10', protocol: 'UDP', packetSize: 512, anomalyScore: 0.92, timestamp: '2025-10-19 12:45:35' },
  { id: '3', sourceIP: '192.168.1.20', destIP: '8.8.8.8', protocol: 'ICMP', packetSize: 64, anomalyScore: 0.15, timestamp: '2025-10-19 12:45:38' },
  { id: '4', sourceIP: '172.16.0.100', destIP: '192.168.1.5', protocol: 'TCP', packetSize: 2048, anomalyScore: 0.78, timestamp: '2025-10-19 12:45:40' },
];

export const mockAnomalies = [
  { id: '1', type: 'File Modification', severity: 'high', confidence: 0.94, feature: 'Unauthorized sudo binary change', timestamp: '2025-10-19 11:45' },
  { id: '2', type: 'Network Spike', severity: 'critical', confidence: 0.96, feature: 'Unusual outbound traffic to external IP', timestamp: '2025-10-19 12:30' },
  { id: '3', type: 'Permission Change', severity: 'medium', confidence: 0.78, feature: 'Config file permissions altered', timestamp: '2025-10-19 10:15' },
];

export const mockIncidents = [
  { id: 'INC-001', type: 'Intrusion Attempt', severity: 'critical', status: 'open', host: '192.168.1.105', detectedTime: '2025-10-19 12:30', assignee: 'analyst' },
  { id: 'INC-002', type: 'File Tampering', severity: 'high', status: 'investigating', host: 'web-server-01', detectedTime: '2025-10-19 11:45', assignee: 'admin' },
  { id: 'INC-003', type: 'Privilege Escalation', severity: 'critical', status: 'contained', host: 'db-server-02', detectedTime: '2025-10-19 09:20', assignee: 'admin' },
  { id: 'INC-004', type: 'Suspicious Login', severity: 'medium', status: 'closed', host: '192.168.1.50', detectedTime: '2025-10-18 22:15', assignee: 'analyst' },
  { id: 'INC-005', type: 'Data Exfiltration', severity: 'high', status: 'open', host: 'file-server-03', detectedTime: '2025-10-19 08:00', assignee: 'analyst' },
];

export const mockUsers = [
  { id: '1', username: 'admin', role: 'admin', lastLogin: '2025-10-19 12:00', status: 'active' },
  { id: '2', username: 'analyst', role: 'analyst', lastLogin: '2025-10-19 11:30', status: 'active' },
  { id: '3', username: 'viewer', role: 'viewer', lastLogin: '2025-10-19 10:00', status: 'active' },
  { id: '4', username: 'john.doe', role: 'analyst', lastLogin: '2025-10-18 16:45', status: 'active' },
];

export const mockAuditLogs = [
  { id: '1', timestamp: '2025-10-19 12:45:32', user: 'admin', action: 'Isolated Host', module: 'Network Monitoring', result: 'success' },
  { id: '2', timestamp: '2025-10-19 12:30:15', user: 'analyst', action: 'Acknowledged Alert', module: 'Incident Management', result: 'success' },
  { id: '3', timestamp: '2025-10-19 11:45:00', user: 'system', action: 'Anomaly Detected', module: 'AI Detection', result: 'alert' },
  { id: '4', timestamp: '2025-10-19 10:15:22', user: 'admin', action: 'Updated Configuration', module: 'System Config', result: 'success' },
];

export const mockChartData = {
  fileChanges: [
    { time: '00:00', changes: 12 },
    { time: '04:00', changes: 8 },
    { time: '08:00', changes: 15 },
    { time: '12:00', changes: 23 },
    { time: '16:00', changes: 18 },
    { time: '20:00', changes: 10 },
  ],
  networkTraffic: [
    { time: '00:00', normal: 450, suspicious: 5 },
    { time: '04:00', normal: 320, suspicious: 2 },
    { time: '08:00', normal: 680, suspicious: 12 },
    { time: '12:00', normal: 890, suspicious: 28 },
    { time: '16:00', normal: 750, suspicious: 15 },
    { time: '20:00', normal: 520, suspicious: 8 },
  ],
  severityDistribution: [
    { name: 'Critical', value: 5 },
    { name: 'High', value: 12 },
    { name: 'Medium', value: 18 },
    { name: 'Low', value: 35 },
  ],
};
