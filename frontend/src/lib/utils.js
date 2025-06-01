// 格式化價格顯示
export const formatPrice = (price) => {
  return new Intl.NumberFormat('zh-TW', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(price);
};

// 格式化百分比
export const formatPercent = (percent) => {
  const sign = percent >= 0 ? '+' : '';
  return `${sign}${percent.toFixed(1)}%`;
};

// 格式化時間
export const formatTime = (timestamp) => {
  const date = new Date(timestamp);
  return date.toLocaleString('zh-TW', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

// 格式化數量
export const formatQuantity = (quantity) => {
  return new Intl.NumberFormat('zh-TW').format(quantity);
};

// 獲取價格變動的顏色類別
export const getPriceColorClass = (change) => {
  if (change > 0) return 'text-green-400';
  if (change < 0) return 'text-red-400';
  return 'text-gray-300';
};

// 獲取價格變動的背景顏色類別
export const getPriceBgColorClass = (change) => {
  if (change > 0) return 'bg-green-900/30';
  if (change < 0) return 'bg-red-900/30';
  return 'bg-gray-800';
};

// 產生隨機ID
export const generateId = () => {
  return Math.random().toString(36).substr(2, 9);
};

// 驗證表單資料
export const validateForm = (data, rules) => {
  const errors = {};
  
  Object.keys(rules).forEach(field => {
    const rule = rules[field];
    const value = data[field];
    
    if (rule.required && (!value || value.toString().trim() === '')) {
      errors[field] = `${rule.label || field} 為必填項目`;
    }
    
    if (rule.min && value < rule.min) {
      errors[field] = `${rule.label || field} 不能小於 ${rule.min}`;
    }
    
    if (rule.max && value > rule.max) {
      errors[field] = `${rule.label || field} 不能大於 ${rule.max}`;
    }
    
    if (rule.pattern && !rule.pattern.test(value)) {
      errors[field] = `${rule.label || field} 格式不正確`;
    }
  });
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};

// 深拷貝對象
export const deepClone = (obj) => {
  return JSON.parse(JSON.stringify(obj));
};

// 防抖函數
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// 節流函數
export const throttle = (func, limit) => {
  let inThrottle;
  return function() {
    const args = arguments;
    const context = this;
    if (!inThrottle) {
      func.apply(context, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};
