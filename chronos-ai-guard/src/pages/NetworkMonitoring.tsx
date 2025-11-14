import { DashboardLayout } from '@/components/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { mockNetworkTraffic } from '@/lib/mockData';
import { Shield, Eye } from 'lucide-react';

const NetworkMonitoring = () => {
  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'destructive';
    if (score >= 0.5) return 'secondary';
    return 'default';
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Network Monitoring</h1>
            <p className="text-muted-foreground">Real-time network traffic analysis</p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Live Network Traffic (Row Data Displayed) Dynamic feature comming soon...</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Source IP</TableHead>
                  <TableHead>Destination IP</TableHead>
                  <TableHead>Protocol</TableHead>
                  <TableHead>Packet Size</TableHead>
                  <TableHead>Anomaly Score</TableHead>
                  <TableHead>Timestamp</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {mockNetworkTraffic.map((traffic) => (
                  <TableRow key={traffic.id}>
                    <TableCell className="font-mono text-sm">{traffic.sourceIP}</TableCell>
                    <TableCell className="font-mono text-sm">{traffic.destIP}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{traffic.protocol}</Badge>
                    </TableCell>
                    <TableCell>{traffic.packetSize} bytes</TableCell>
                    <TableCell>
                      <Badge variant={getScoreColor(traffic.anomalyScore)}>
                        {(traffic.anomalyScore * 100).toFixed(0)}%
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">{traffic.timestamp}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm">
                          <Shield className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default NetworkMonitoring;
