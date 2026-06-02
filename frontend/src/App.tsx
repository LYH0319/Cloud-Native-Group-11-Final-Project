import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Login } from './pages/login';
import { Admin } from './pages/admin';
import { DeveloperHome } from './pages/developerHome';
import { DeveloperAddRESTfulAPI } from './pages/developerAddRESTfulAPI';
import { DeveloperAddShellScript } from './pages/developerAddShellScript';
import { Operator } from './pages/operator';
import { RouteGuard } from './components/routeGuard';

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />

        <Route
          path="/admin"
          element={
            <RouteGuard allowedRole="admin">
              <Admin />
            </RouteGuard>
          }
        />

        <Route
          path="/developer"
          element={
            <RouteGuard allowedRole="developer">
              <DeveloperHome />
            </RouteGuard>
          }
        />
        <Route
          path="/developer/RESTfulAPI"
          element={
            <RouteGuard allowedRole="developer">
              <DeveloperAddRESTfulAPI />
            </RouteGuard>
          }
        />
        <Route
          path="/developer/ShellScript"
          element={
            <RouteGuard allowedRole="developer">
              <DeveloperAddShellScript />
            </RouteGuard>
          }
        />

        <Route
          path="/operator"
          element={
            <RouteGuard allowedRole="operator">
              <Operator />
            </RouteGuard>
          }
        />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
