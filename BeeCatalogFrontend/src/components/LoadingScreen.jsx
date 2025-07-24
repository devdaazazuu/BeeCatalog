import React, { useState, useEffect } from 'react';
import { Loader2, Clock, Activity } from 'lucide-react';

const LoadingScreen = ({ isVisible, message = 'Carregando...', showTimer = true, showProgress = false, progress = 0 }) => {
  const [elapsedTime, setElapsedTime] = useState(0);
  const [dots, setDots] = useState('');

  useEffect(() => {
    if (!isVisible) {
      setElapsedTime(0);
      return;
    }

    const timer = setInterval(() => {
      setElapsedTime(prev => prev + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [isVisible]);

  useEffect(() => {
    if (!isVisible) return;

    const dotsTimer = setInterval(() => {
      setDots(prev => {
        if (prev === '...') return '';
        return prev + '.';
      });
    }, 500);

    return () => clearInterval(dotsTimer);
  }, [isVisible]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-gray-800/95 border border-amber-500/30 rounded-xl p-8 shadow-2xl max-w-md w-full mx-4">
        {/* Header com ícone animado */}
        <div className="flex items-center justify-center mb-6">
          <div className="relative">
            <Loader2 className="w-12 h-12 text-amber-400 animate-spin" />
            <Activity className="w-6 h-6 text-amber-300 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 animate-pulse" />
          </div>
        </div>

        {/* Mensagem principal */}
        <div className="text-center mb-6">
          <h3 className="text-xl font-semibold text-white mb-2">
            Processando{dots}
          </h3>
          <p className="text-gray-300 text-sm leading-relaxed">
            {message}
          </p>
        </div>

        {/* Barra de progresso (se habilitada) */}
        {showProgress && (
          <div className="mb-6">
            <div className="flex justify-between text-xs text-gray-400 mb-2">
              <span>Progresso</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-amber-400 to-amber-500 h-2 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${Math.min(progress, 100)}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* Timer */}
        {showTimer && (
          <div className="flex items-center justify-center space-x-2 text-gray-400">
            <Clock className="w-4 h-4" />
            <span className="text-sm font-mono">
              Tempo decorrido: {formatTime(elapsedTime)}
            </span>
          </div>
        )}

        {/* Indicador de atividade */}
        <div className="mt-4 flex justify-center space-x-1">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="w-2 h-2 bg-amber-400 rounded-full animate-pulse"
              style={{
                animationDelay: `${i * 0.2}s`,
                animationDuration: '1s'
              }}
            ></div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default LoadingScreen;