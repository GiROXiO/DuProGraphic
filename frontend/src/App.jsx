import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import LoginView from "./components/main_views/LoginView";
import FeedView from "./components/main_views/FeedView";
import JobsView from "./components/main_views/JobsView";
import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginView />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<FeedView />} />
          <Route path="/jobs" element={<JobsView />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
