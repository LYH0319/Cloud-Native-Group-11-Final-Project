export const styles = {
  header: {
    backgroundColor: '#00007A', // 登入頁的深藍色
    color: 'white',
    padding: '12px 24px',
    fontSize: '30px',
    fontWeight: 'bold',
    display: 'flex', // 啟動 Flex 佈局
    justifyContent: 'space-between', // 讓內容左右分開
    alignItems: 'center', // 垂直置中
    fontFamily: 'sans-serif'
  },
  container: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    marginTop: '40px',
    fontFamily: 'sans-serif'
  },
  title: {
    fontSize: '24px',
    fontWeight: 'bold',
    marginBottom: '15px',
    color: '#000'
  },
  input: {
    width: '280px',
    padding: '8px 12px',
    fontSize: '18px',
    color: 'black',
    backgroundColor: 'white',
    border: '1px solid #b5b5b5',
    marginBottom: '15px',
    outline: 'none'
  },
  buttonForm: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    width: '100%'
  },
  primaryBtn: {
    backgroundColor: '#00A2E8',
    color: 'white',
    border: 'none',
    borderRadius: '20px',
    padding: '8px 0',
    width: '200px',
    fontSize: '14px',
    marginBottom: '12px',
    cursor: 'pointer',
    transition: 'background-color 0.2s'
  }
};

export const homeLoginLogoutStyles = {
  style: {
    color: '#00007A',
    fontWeight: 'bold',
    borderRadius: '20px'
  }
};

const theme = {
  primaryBlue: '#0f117a',
  borderColor: '#cccccc'
};

export const loginStyles = {
  pageContainer: {
    width: '100vw',
    height: '100vh',
    margin: 0,
    padding: 0,
    overflow: 'hidden' as const,
    backgroundColor: '#f0f0f0',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center'
  },

  outerBox: {
    width: '100%',
    height: '100%',
    backgroundColor: theme.primaryBlue,
    padding: '30px', // 調整最外層深藍色邊框的厚度
    boxSizing: 'border-box' as const
  },

  whiteGap: {
    width: '100%',
    height: '100%',
    backgroundColor: '#fff',
    padding: '20px', // 灰色框線與深藍色框線之間的白色留白
    boxSizing: 'border-box' as const
  },

  innerBorder: {
    width: '100%',
    height: '100%',
    border: `8px solid ${theme.primaryBlue}`, // 內層深藍色主框線
    display: 'flex',
    flexDirection: 'row' as const, // 確保左右兩個 Panel 水平並排
    alignItems: 'center', // 垂直置中
    position: 'relative' as const,
    boxSizing: 'border-box' as const,
    backgroundColor: '#fff'
  },

  leftPanel: {
    width: '45%', // 調整左側寬度比例
    height: '100%',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center'
  },

  leftBox: {
    backgroundColor: theme.primaryBlue,
    border: '6px solid #fff', // 白色內層邊框
    outline: `6px solid ${theme.primaryBlue}`, // 深藍色外層邊框
    width: '75%', // 加寬藍色方塊
    height: '60%', // 加高藍色方塊
    display: 'flex',
    flexDirection: 'column' as const,
    justifyContent: 'center',
    alignItems: 'center'
  },

  leftBoxText: {
    color: '#fff',
    margin: '10px 0',
    fontSize: '48px', // 顯著放大字體以符合圖片比例
    fontWeight: 'bold',
    width: '100%',
    textAlign: 'center' as const
  },

  rightPanel: {
    width: '55%', // 調整右側寬度比例
    height: '100%',
    display: 'flex',
    flexDirection: 'column' as const,
    justifyContent: 'center',
    paddingLeft: '5%',
    paddingRight: '15%', // 右側增加留白，讓輸入框偏向中心對齊
    boxSizing: 'border-box' as const
  },

  formContainer: {
    width: '100%'
  },

  title: {
    color: theme.primaryBlue,
    fontSize: '32px', // 放大歡迎使用字體
    fontWeight: 'bold',
    marginBottom: '20px'
  },

  subtitle: {
    color: '#666',
    fontSize: '16px',
    marginBottom: '16px'
  },

  input: {
    width: '100%',
    padding: '15px 20px', // 增加輸入框內的上下左右留白
    fontSize: '20px', // 放大輸入框內的字體
    border: `2px solid ${theme.borderColor}`, // 加深邊框
    outline: 'none',
    color: '#333',
    backgroundColor: '#fff',
    boxSizing: 'border-box' as const,
    marginBottom: '15px'
  },

  buttonContainer: {
    display: 'flex',
    justifyContent: 'flex-end', // 按鈕靠右對齊
    gap: '15px' // 加入兩個按鈕（上一部/下一部）之間的間距
  },

  primaryBtn: {
    backgroundColor: theme.primaryBlue,
    color: '#ffffff',
    border: 'none',
    borderRadius: '25px', // 使按鈕呈圓潤的藥丸形狀
    padding: '12px 35px',
    fontSize: '18px',
    cursor: 'pointer'
  },

  errorMsg: {
    color: '#dc3545',
    fontSize: '14px',
    marginBottom: '12px',
    fontWeight: 'bold'
  },

  successContainer: {
    textAlign: 'center' as const
  },

  successIcon: {
    display: 'inline-block',
    marginBottom: '20px'
  },

  successTitle: {
    color: '#198754',
    fontWeight: 'bold'
  },

  successText: {
    color: '#888',
    fontSize: '14px'
  },

  forgotPasswordContainer: {
    position: 'absolute' as const,
    bottom: '40px',
    right: '50px',
    color: theme.primaryBlue, // 改為與圖片相同的深藍色
    fontWeight: 'bold', // 加粗體
    cursor: 'pointer'
  }
};

export const operatorStyles = {
  header: {
    backgroundColor: '#00007A', // 系統經典深藍色
    color: 'white',
    padding: '16px 32px',
    fontSize: '26px',
    fontWeight: 'bold' as const,
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    fontFamily: 'sans-serif',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
  },
  headerRight: {
    display: 'flex',
    gap: '20px',
    alignItems: 'center',
    fontSize: '16px'
  },
  logoutBtn: {
    backgroundColor: 'white',
    color: '#00007A',
    border: 'none',
    borderRadius: '20px',
    padding: '6px 16px',
    fontWeight: 'bold' as const,
    cursor: 'pointer'
  },
  container: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    backgroundColor: '#F8F9FA', // 淺灰底色，襯托出白色卡片
    minHeight: 'calc(100vh - 70px)',
    padding: '40px 20px',
    fontFamily: 'sans-serif'
  },
  dashboardCard: {
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)', // 仿照圖片的立體卡片陰影
    width: '100%',
    maxWidth: '1100px',
    padding: '30px',
    boxSizing: 'border-box' as const
  },
  title: {
    fontSize: '24px',
    fontWeight: 'bold' as const,
    color: '#333',
    marginBottom: '8px'
  },
  subtitle: {
    fontSize: '14px',
    color: '#666',
    marginBottom: '24px'
  },
  systemStatus: {
    backgroundColor: '#E6F4EA',
    color: '#137333',
    padding: '12px 20px',
    borderRadius: '6px',
    fontSize: '14px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '25px',
    fontWeight: 'bold' as const
  },
  jobTable: {
    width: '100%',
    borderCollapse: 'collapse' as const,
    marginTop: '15px',
    textAlign: 'left' as const
  },
  th: {
    borderBottom: '2px solid #E0E0E0',
    padding: '12px 8px',
    color: '#555',
    fontSize: '15px',
    fontWeight: 'bold' as const
  },
  td: {
    borderBottom: '1px solid #EEEEEE',
    padding: '16px 8px',
    fontSize: '14px',
    color: '#333',
    verticalAlign: 'top' as const
  },
  badge: (method: string) => {
    const colors: Record<string, string> = {
      GET: '#0B6623',
      POST: '#3366CC',
      PUT: '#DD9900',
      DELETE: '#CC3333',
      PATCH: '#883399'
    };
    return {
      backgroundColor: colors[method] || '#666',
      color: 'white',
      padding: '3px 8px',
      borderRadius: '4px',
      fontSize: '11px',
      fontWeight: 'bold' as const,
      marginRight: '6px'
    };
  },
  statusBadge: (status: string) => {
    const colors: Record<string, { bg: string; text: string }> = {
      閒置中: { bg: '#E8EAED', text: '#3C4043' },
      執行中: { bg: '#E8F0FE', text: '#1A73E8' },
      執行成功: { bg: '#E6F4EA', text: '#137333' },
      執行失敗: { bg: '#FCE8E6', text: '#C5221F' }
    };
    const style = colors[status] || colors['閒置中'];
    return {
      backgroundColor: style.bg,
      color: style.text,
      padding: '4px 10px',
      borderRadius: '12px',
      fontSize: '12px',
      fontWeight: 'bold' as const
    };
  },
  triggerBtn: {
    backgroundColor: '#00007A', // 與圖片按紐同色系的深藍
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    padding: '8px 14px',
    fontSize: '13px',
    cursor: 'pointer',
    fontWeight: 'bold' as const,
    transition: 'background-color 0.2s',
    whiteSpace: 'nowrap' as const
  },
  detailText: {
    fontSize: '12px',
    color: '#666',
    marginTop: '4px',
    lineHeight: '1.5'
  },
  codeBlock: {
    fontFamily: 'monospace',
    backgroundColor: '#F5F5F5',
    padding: '6px',
    borderRadius: '4px',
    fontSize: '11px',
    marginTop: '4px',
    whiteSpace: 'pre-wrap' as const,
    wordBreak: 'break-all' as const
  }
};

export default {
  styles,
  homeLoginLogoutStyles,
  loginStyles,
  operatorStyles
};
