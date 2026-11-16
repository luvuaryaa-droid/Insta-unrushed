import React from 'react';
import { Composition } from 'remotion';
import { Film } from './Film';
import { DURATION_S, FPS } from './lib';

export const Root: React.FC = () => (
  <Composition id="Ocean" component={Film} durationInFrames={Math.round(DURATION_S * FPS)} fps={FPS} width={1920} height={1080} />
);
