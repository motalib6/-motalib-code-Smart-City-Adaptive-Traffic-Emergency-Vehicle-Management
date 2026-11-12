export type Role = 'admin' | 'operator' | 'viewer';
export type Phase = 'GREEN_NS' | 'YELLOW_NS' | 'ALL_RED_TO_EW' | 'GREEN_EW' | 'YELLOW_EW' | 'ALL_RED_TO_NS';
export type SignalColor = 'green' | 'yellow' | 'red';
export type Scenario = 'normal' | 'medium' | 'rush' | 'heavy' | 'unbalanced' | 'emergency';
export type InputMode = 'sumo' | 'yolo';

export interface User { id: number; username: string; role: Role; }
export interface AuthResponse { access_token: string; token_type: string; user: User; }

export interface ApproachData { approach: 'N' | 'S' | 'E' | 'W'; vehicles: number; queue: number; avgWaitSec: number; demand: number; }
export interface Junction {
  id: string; name: string; phase: Phase; phaseRemainingSec: number;
  greenSec: number; yellowSec: number; allRedSec: number;
  approaches: ApproachData[]; totalVehicles: number; congestion: 'low' | 'moderate' | 'high';
}
export interface VehiclePos { id: string; type: 'car' | 'bus' | 'motorcycle' | 'truck' | 'ambulance'; x: number; y: number; junction: string; speedKmh: number; }
export interface DashboardSummary {
  totalVehicles: number; activeIntersections: number; avgWaitSec: number;
  congestion: 'low' | 'moderate' | 'high'; activeEmergencies: number;
  throughputPerMin: number; mode: InputMode; sumoRunning: boolean;
}
export interface DensityPoint { time: string; vehicles: number; avgWait: number; }
export interface AppEvent { id: number; timestamp: string; type: string; junctionId?: string; source: string; message: string; severity: 'info' | 'warning' | 'critical'; }
export interface Emergency {
  id: string; ambulanceId: string; fromJunction: string; toJunction: string; route: string[];
  status: 'requested' | 'validated' | 'priority_granted' | 'en_route' | 'passed' | 'completed';
  etaSec: number; progressPct: number; currentJunction: string; nextJunction: string; speedKmh: number;
}
export interface Detection { label: 'car' | 'motorcycle' | 'bus' | 'truck'; confidence: number; x: number; y: number; w: number; h: number; lane: 'N' | 'S' | 'E' | 'W'; }
export interface VisionStatus { running: boolean; source: 'upload' | 'webcam' | null; fps: number; detections: Detection[]; counts: Record<string, number>; }
export interface ExperimentRun { id: string; mode: 'fixed' | 'adaptive'; seed: number; durationSec: number; meanWaitSec: number; maxQueue: number; throughput: number; emergencyTravelSec: number | null; createdAt: string; }
export interface AdminSettings { minGreenSec: number; maxGreenSec: number; yellowSec: number; allRedSec: number; demandWQueue: number; demandWCount: number; demandWWait: number; }
export interface LiveEvent { type: string; timestamp: string; junctionId?: string; source?: string; data: unknown; }
