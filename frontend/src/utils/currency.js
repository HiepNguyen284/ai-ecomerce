const vndFormatter = new Intl.NumberFormat('vi-VN', {
  style: 'currency',
  currency: 'VND',
  maximumFractionDigits: 0,
});

export function formatVND(value) {
  const numberValue = Number(value);
  if (Number.isNaN(numberValue)) {
    return vndFormatter.format(0);
  }
  return vndFormatter.format(numberValue);
}
