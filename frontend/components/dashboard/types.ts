export interface User {
  name: string;
  role: 'tinh' | 'xa';
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
}

export interface Channel {
  name: string;
  icon: string;
  color: string;
  sentStr: string;
  deliveredStr: string;
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
}

export interface Hamlet {
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
