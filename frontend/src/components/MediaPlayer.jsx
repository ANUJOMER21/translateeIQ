import { useState, useMemo, useRef, useCallback } from 'react';
import Icon from './Icon';
import { waveformBars } from '../utils/meetingUtils';

const fmt = (s) => {
  if (!isFinite(s) || s < 0) return '--:--';
  const m = Math.floor(s / 60), sec = Math.floor(s % 60);
  return `${m}:${sec.toString().padStart(2, '0')}`;
};

const MediaPlayer = ({ url, fileType }) => {
  const mediaRef = useRef(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [ready, setReady] = useState(false);
  const [volume, setVolume] = useState(1);
  const bars = useMemo(() => waveformBars(80), []);

  const toggle = useCallback(() => {
    const el = mediaRef.current;
    if (!el) return;
    if (el.paused) { el.play(); }
    else { el.pause(); }
  }, []);

  const seek = useCallback((e) => {
    const el = mediaRef.current;
    if (!el || !duration) return;
    const rect = e.currentTarget.getBoundingClientRect();
    el.currentTime = ((e.clientX - rect.left) / rect.width) * duration;
  }, [duration]);

  const skip = (delta) => {
    const el = mediaRef.current;
    if (!el) return;
    el.currentTime = Math.max(0, Math.min(duration, el.currentTime + delta));
  };

  const mediaProps = {
    ref: mediaRef,
    src: url,
    onTimeUpdate: e => setCurrentTime(e.target.currentTime),
    onDurationChange: e => setDuration(e.target.duration),
    onCanPlay: () => setReady(true),
    onEnded: () => setPlaying(false),
    onPause: () => setPlaying(false),
    onPlay: () => setPlaying(true),
    preload: 'metadata',
  };

  return (
    <div className="media-player">
      {fileType === 'video'
        ? <video {...mediaProps} className="media-player__video" />
        : <audio {...mediaProps} style={{ display: 'none' }} />
      }

      {/* Seekable waveform */}
      <div
        className="player__waveform"
        onClick={seek}
        style={{ cursor: 'pointer', flex: 1 }}
        title="Click to seek"
        role="slider"
        aria-label="Seek"
        aria-valuenow={Math.round(currentTime)}
        aria-valuemax={Math.round(duration)}
      >
        {bars.map((h, i) => {
          const ratio = duration ? currentTime / duration : 0;
          return (
            <div
              key={i}
              className={`bar${i / bars.length < ratio ? ' played' : ''}`}
              style={{ height: `${h * 100}%` }}
            />
          );
        })}
      </div>

      {/* Controls */}
      <div className="media-player__controls">
        <div className="player__controls">
          <button className="player__btn" onClick={() => skip(-10)} title="−10s" aria-label="Back 10s">
            <Icon name="skip-back" size={15} />
          </button>
          <button
            className="player__btn player__btn--play"
            onClick={toggle}
            disabled={!ready}
            title={playing ? 'Pause' : 'Play'}
            aria-label={playing ? 'Pause' : 'Play'}
          >
            <Icon name={playing ? 'pause' : 'play'} size={18} />
          </button>
          <button className="player__btn" onClick={() => skip(10)} title="+10s" aria-label="Forward 10s">
            <Icon name="skip-fwd" size={15} />
          </button>
        </div>

        <div className="player__time">
          <b>{fmt(currentTime)}</b>&nbsp;/&nbsp;{fmt(duration)}
        </div>

        <div className="media-player__vol">
          <Icon name="audio" size={13} style={{ color: 'var(--fg-3)', flexShrink: 0 }} />
          <input
            type="range" min="0" max="1" step="0.05"
            value={volume}
            onChange={e => {
              const v = parseFloat(e.target.value);
              setVolume(v);
              if (mediaRef.current) mediaRef.current.volume = v;
            }}
            className="media-player__vol-slider"
            aria-label="Volume"
          />
        </div>
      </div>
    </div>
  );
};

export default MediaPlayer;
