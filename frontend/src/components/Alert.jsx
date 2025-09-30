import React from 'react';

const Alert = ({ type = 'info', message }) => {
  if (!message) return null;
  const className = `alert alert-${type} mt-3`;
  return (
    <div className={className} role="alert">
      {message}
    </div>
  );
};

export default Alert;
