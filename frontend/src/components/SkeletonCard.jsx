/* =========================================================
   SkeletonCard — loading placeholder component
   Props:
     variant: 'product' | 'routine' | 'chat' | 'stat'
   Classes from kimi-components.css
   ========================================================= */

function SkeletonProduct() {
  return (
    <div className="skeleton-product">
      <div className="skeleton sk-img" />
      <div className="skeleton sk-title" />
      <div className="skeleton sk-price" />
      <div className="skeleton sk-btn" />
    </div>
  );
}

function SkeletonRoutine() {
  return (
    <div className="skeleton-product skeleton-routine">
      <div className="skeleton sk-img" />
      <div className="skeleton sk-name" />
      <div className="sk-badges">
        <div className="skeleton sk-badge" />
        <div className="skeleton sk-badge" />
      </div>
    </div>
  );
}

function SkeletonChat() {
  return (
    <div className="skeleton-product">
      <div className="skeleton-chat">
        <div className="skeleton sk-avatar" />
        <div className="skeleton sk-bubble short" />
      </div>
      <div className="skeleton-chat">
        <div className="skeleton sk-avatar" />
        <div className="skeleton sk-bubble" />
      </div>
      <div className="skeleton-chat">
        <div className="skeleton sk-avatar" />
        <div className="skeleton sk-bubble short" />
      </div>
    </div>
  );
}

function SkeletonStat() {
  return (
    <div className="skeleton-product skeleton-stat">
      <div className="skeleton sk-number" />
      <div className="skeleton sk-label" />
    </div>
  );
}

const VARIANTS = {
  product: SkeletonProduct,
  routine: SkeletonRoutine,
  chat:    SkeletonChat,
  stat:    SkeletonStat,
};

export default function SkeletonCard({ variant = "product" }) {
  const Component = VARIANTS[variant] || SkeletonProduct;
  return <Component />;
}
