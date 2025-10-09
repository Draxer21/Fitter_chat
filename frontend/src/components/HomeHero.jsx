import React from 'react';
import '../styles/hero.css';
import { useLocale } from '../contexts/LocaleContext';

export default function HomeHero() {
  const { t } = useLocale();

  const style = {
    backgroundImage: "linear-gradient(rgba(0,0,0,0.45), rgba(0,0,0,0.45)), url('/gym.jpg')",
    backgroundSize: 'cover',
    backgroundPosition: 'center center',
  };

  return (
    <header className="home-hero" style={style}>
      <div className="hero-overlay" />
      <div className="hero-inner container">
        <div className="hero-content">
          <h1 className="hero-title">
            <span className="muted">{t('home.hero.title.muted')}</span>{' '}
            <span className="highlight">{t('home.hero.title.highlight')}</span>
          </h1>
          <h2 className="hero-sub">
            {t('home.hero.subtitle.prefix')}{' '}
            <strong>{t('home.hero.subtitle.strong')}</strong>
          </h2>
          <p className="hero-desc">{t('home.hero.description')}</p>
          <div className="hero-cta">
            <a className="btn btn-outline-dark btn-lg" href="/registro">
              {t('home.hero.cta')}
            </a>
          </div>
        </div>
      </div>

      <div className="hero-features container">
        <div className="row">
          <div className="col-md-3 feature">
            <h5>{t('home.hero.feature.training.title')}</h5>
            <p>{t('home.hero.feature.training.desc')}</p>
          </div>
          <div className="col-md-3 feature">
            <h5>{t('home.hero.feature.ai.title')}</h5>
            <p>{t('home.hero.feature.ai.desc')}</p>
          </div>
          <div className="col-md-3 feature">
            <h5>{t('home.hero.feature.gym.title')}</h5>
            <p>{t('home.hero.feature.gym.desc')}</p>
          </div>
          <div className="col-md-3 feature">
            <h5>{t('home.hero.feature.community.title')}</h5>
            <p>{t('home.hero.feature.community.desc')}</p>
          </div>
        </div>
      </div>
    </header>
  );
}
