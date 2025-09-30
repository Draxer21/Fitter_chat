import React from 'react';


const Logo = ({ src = '/fitter_logo.png', alt = 'Fitter', width, height, className, style, ...props }) => {
  const handleError = (e) => {
    e.currentTarget.onerror = null;
    e.currentTarget.src = '/logo192.png';
  };

  return (
    <img
      src={src}
      alt={alt}
      width={width}
      height={height}
      className={className}
      style={style}
      onError={handleError}
      {...props}
    />
  );
};

export default Logo;
