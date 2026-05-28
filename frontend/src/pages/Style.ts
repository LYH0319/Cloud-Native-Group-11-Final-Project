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