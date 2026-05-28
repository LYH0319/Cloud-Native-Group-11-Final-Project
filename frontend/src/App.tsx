import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Home } from './pages/home';
import { Login } from './pages/login';
import { Developer } from './pages/developer';
import { Operator } from './pages/operator';
import { RouteGuard } from './components/routeGuard';

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />

        <Route path="/developer" element={
          <RouteGuard allowedRole="developer">
            <Developer />
          </RouteGuard>
        } />

        <Route path="/operator" element={
          <RouteGuard allowedRole="operator">
            <Operator />
          </RouteGuard>
        } />
      </Routes>
    </BrowserRouter>
  );
};

export default App;