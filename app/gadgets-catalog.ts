export interface GadgetItem {
  id: 'earpods' | 'human' | string;
  title: string;
  category: string;
  badge: string;
  subtitle: string;
  pieces: number;
  subsystems: number;
  status: 'ready' | 'upcoming';
  description: string;
  dataUrl?: string;
  specsUrl?: string;
  sourceLabel?: string;
}

export const GADGET_LIBRARY: GadgetItem[] = [
  {
    id: 'earpods',
    title: 'AirPods Pro (2nd Gen)',
    category: 'Audio & Acoustics',
    badge: 'CAD DECONSTRUCTION',
    subtitle: 'AUTHENTIC CAD SPEC · HOW THINGS WORK',
    pieces: 13,
    subsystems: 6,
    status: 'ready',
    description: 'Deconstructed Apple AirPods Pro 2 CAD model featuring the Apple H2 computational audio SiP, custom 11mm dynamic transducer, silicone umbrella tips, and laser-cut acoustic vents.',
    dataUrl: '/models/earpods.json',
    specsUrl: 'https://www.apple.com/airpods-pro/',
    sourceLabel: 'Apple Accessory Design Specifications'
  },
  {
    id: 'human',
    title: 'Human Anatomy Atlas',
    category: 'Biology & Medicine',
    badge: '3D REFERENCE',
    subtitle: 'ADULT MALE · BODYPARTS3D',
    pieces: 2234,
    subsystems: 12,
    status: 'ready',
    description: 'High-performance 3D atlas of the adult human body deconstructed across skeletal, muscular, cardiovascular, nervous, and organ systems.',
    dataUrl: '/models/atlas.json',
    specsUrl: 'https://lifesciencedb.jp/bp3d/',
    sourceLabel: 'BodyParts3D (DBCLS)'
  },
  {
    id: 'iphone',
    title: 'Titanium Smartphone',
    category: 'Consumer Electronics',
    badge: 'IN DEVELOPMENT',
    subtitle: 'A17 PRO · MULTI-LAYER LOGIC · PERISCOPE',
    pieces: 18,
    subsystems: 7,
    status: 'upcoming',
    description: 'Upcoming gadget deconstruction: Grade 5 titanium frame, stacked substrate-like PCB logic boards, tetraprism periscope camera zoom assembly, and graphite vapor chamber.',
  },
  {
    id: 'chronograph',
    title: 'Mechanical Automatic Chronograph',
    category: 'Horology & Micro-mechanics',
    badge: '3D DECONSTRUCTION',
    subtitle: '28-JEWEL MOVEMENT · 28,800 VPH',
    pieces: 14,
    subsystems: 7,
    status: 'ready',
    description: 'High-precision deconstruction of an automatic mechanical chronograph: 28,800 vph Glucydur balance wheel, Nivarox hairspring, Swiss lever escapement, 4-wheel gear train, column-wheel chronograph clutch, and heavy tungsten oscillating winding rotor.',
    dataUrl: '/models/chronograph.json',
    sourceLabel: 'Haute Horlogerie Calibre Spec'
  },
  {
    id: 'fpv_drone',
    title: 'Brushless FPV Drone Motor',
    category: 'Robotics & Aerospace',
    badge: 'COMING SOON',
    subtitle: 'CURVED N52H MAGNETS · 12-POLE STATOR',
    pieces: 12,
    subsystems: 4,
    status: 'upcoming',
    description: 'Upcoming robotics deconstruction: CNC bell with N52H arc neodymium magnets, 12-slot stator copper windings, hollow titanium shaft, and high-RPM ball bearings.',
  }
];
