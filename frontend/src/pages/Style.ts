export const styles = {
  header: {
    backgroundColor: '#00007A', // 登入頁的深藍色
    color: 'white',
    padding: '12px 24px',
    fontSize: '30px',
    fontWeight: 'bold',
    display: 'flex',            // 啟動 Flex 佈局
    justifyContent: 'space-between', // 讓內容左右分開
    alignItems: 'center',       // 垂直置中
    fontFamily: 'sans-serif',
  },
  container: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    marginTop: '40px',
    fontFamily: 'sans-serif',
  },
  title: {
    fontSize: '24px',
    fontWeight: 'bold',
    marginBottom: '15px',
    color: '#000',
  },
  input: {
    width: '280px',
    padding: '8px 12px',
    fontSize: '18px',
    color: 'black',
    backgroundColor: 'white',
    border: '1px solid #b5b5b5',
    marginBottom: '15px',
    outline: 'none',
  },
  buttonForm: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    width: '100%',
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
    transition: 'background-color 0.2s',
  },
};

export const homeLoginLogoutStyles = {
  style: {
    color: '#00007A', 
    fontWeight: 'bold', 
    borderRadius: '20px'
  }
}

const theme = {
  primaryBlue: '#0f117a',
  borderColor: '#cccccc',
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
    alignItems: 'center',
  },
  
  outerBox: {
    width: '100%',   
    height: '100%',  
    backgroundColor: theme.primaryBlue,
    padding: '30px', // 調整最外層深藍色邊框的厚度
    boxSizing: 'border-box' as const, 
  },

  whiteGap: {
    width: '100%',
    height: '100%',
    backgroundColor: '#fff',
    padding: '20px', // 灰色框線與深藍色框線之間的白色留白
    boxSizing: 'border-box' as const,
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
    backgroundColor: '#fff',
  },
  
  leftPanel: {
    width: '45%', // 調整左側寬度比例
    height: '100%',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
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
    alignItems: 'center',
  },
  
  leftBoxText: {
    color: '#fff',
    margin: '10px 0',
    fontSize: '48px', // 顯著放大字體以符合圖片比例
    fontWeight: 'bold',
    width: '100%', 
    textAlign: 'center' as const, 
  },
  
  rightPanel: {
    width: '55%', // 調整右側寬度比例
    height: '100%',
    display: 'flex',
    flexDirection: 'column' as const,
    justifyContent: 'center',
    paddingLeft: '5%',
    paddingRight: '15%', // 右側增加留白，讓輸入框偏向中心對齊
    boxSizing: 'border-box' as const,
  },
  
  formContainer: {
    width: '100%',
  },
  
  title: {
    color: theme.primaryBlue,
    fontSize: '32px', // 放大歡迎使用字體
    fontWeight: 'bold',
    marginBottom: '20px', 
  },
  
  subtitle: {
    color: '#666',
    fontSize: '16px', 
    marginBottom: '16px', 
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
    marginBottom: '15px', 
  },
  
  buttonContainer: {
    display: 'flex',
    justifyContent: 'flex-end', // 按鈕靠右對齊
    gap: '15px', // 加入兩個按鈕（上一部/下一部）之間的間距
  },
  
  primaryBtn: {
    backgroundColor: theme.primaryBlue,
    color: '#ffffff',
    border: 'none',
    borderRadius: '25px', // 使按鈕呈圓潤的藥丸形狀
    padding: '12px 35px', 
    fontSize: '18px', 
    cursor: 'pointer',
  },
  
  errorMsg: {
    color: '#dc3545',
    fontSize: '14px',
    marginBottom: '12px',
    fontWeight: 'bold',
  },
  
  successContainer: {
    textAlign: 'center' as const,
  },
  
  successIcon: {
    display: 'inline-block',
    marginBottom: '20px',
  },
  
  successTitle: {
    color: '#198754',
    fontWeight: 'bold',
  },
  
  successText: {
    color: '#888',
    fontSize: '14px',
  },
  
  forgotPasswordContainer: {
    position: 'absolute' as const,
    bottom: '40px',
    right: '50px',
    color: theme.primaryBlue, // 改為與圖片相同的深藍色
    fontWeight: 'bold', // 加粗體
    cursor: 'pointer',
  },
};

export default {
  styles,
  homeLoginLogoutStyles,
  loginStyles
};