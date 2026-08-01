export interface User {
  id?: string | number;
  name: string;
  role: 'tinh' | 'xa';
  commune_id?: string | number;
}

export interface Kpi {
  label: string;
  icon: string;
  value: string;
  sub: string;
  cardStyle: string;
  valueColor: string;
}

export interface Commune {
  id: string | number;
  name: string;
  icon: string;
  hazard: string;
  popStr: string;
  receivedStr: string;
  notReceivedStr: string;
  notReceivedColor: string;
  rateStr: string;
  rateColor: string;
  statusLabel: string;
  pillStyle: string;
  lat: number;
  lng: number;
  pop: number;
  received?: number | null;
}

export interface Channel {
  name: string;
  icon: string;
  color: string;
  pendingStr: string;
  sentStr: string;
  deliveredStr: string;
  receivedStr: string;
  failedStr: string;
  rateStr: string;
  pct: string;
}

export interface Ethnic {
  name: string;
  popStr: string;
  pct: string;
}

export interface Activity {
  icon: string;
  bg: string;
  text: string;
  time: string;
}

export interface Policy {
  code: string;
  title: string;
  type: string;
  by: string;
  start: string;
  end: string;
  status: string;
  statusLabel: string;
  pillStyle: string;
}

export interface Log {
  time: string;
  commune: string;
  channel: string;
  channelIcon: string;
  ethnic: string;
  recipientsStr: string;
  pendingStr: string;
  sentStr: string;
  receivedStr: string;
  failedStr: string;
  trackingAvailable: boolean;
  statusLabel: string;
  pillStyle: string;
}

export interface DashboardData {
  kpis: Kpi[];
  communes: Commune[];
  channels: Channel[];
  ethnics: Ethnic[];
  activities: Activity[];
  policies: Policy[];
  logs: Log[];
  alertCount: number;
  alertHeadline: string;
  timeText: string;
  policyActive: number;
  policyExpiring: number;
  policyExpired: number;
  predictions?: any[];
}

export interface Hamlet {
  id: number;
  name: string;
  headman: string;
  rateStr: string;
  rateColor: string;
  confirmLabel: string;
}

export interface LostPerson {
  name: string;
  coord: string;
  phone: string;
}

export interface DetailData {
  id: string | number;
  icon: string;
  name: string;
  hazard: string;
  popStr: string;
  receivedStr: string;
  notReceivedStr: string;
  notReceivedColor: string;
  rateStr: string;
  rateColor: string;
  hamletCount: number;
  hamlets: Hamlet[];
  hasLost: boolean;
  lostCount: number;
  lost: LostPerson[];
  headBg: string;
}
