import { useState, useEffect } from "react";
import { Routes, Route } from "react-router-dom";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import {
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Box,
  Container,
} from "@mui/material";
import Navbar from "../components/Navbar";
import Dashboard from "../components/Dashboard";
import LogViewer from "../components/LogViewer";
import Analytics from "../components/Analytics";
import Settings from "../components/Settings";
import { SocketProvider } from "../contexts/SocketContext";
import "./App.css";

const theme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#1976d2",
    },
    secondary: {
      main: "#dc004e",
    },
    error: {
      main: "#f44336",
    },
    warning: {
      main: "#ff9800",
    },
    info: {
      main: "#2196f3",
    },
    success: {
      main: "#4caf50",
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <SocketProvider>
        <Box
          sx={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}
        >
          <AppBar position="static" elevation={1}>
            <Toolbar>
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                Log Monitoring Dashboard
              </Typography>
            </Toolbar>
          </AppBar>

          <Box sx={{ display: "flex", flex: 1 }}>
            <Navbar />

            <Box
              component="main"
              sx={{ flexGrow: 1, p: 3, backgroundColor: "#f5f5f5" }}
            >
              <Container maxWidth="xl">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/logs" element={<LogViewer />} />
                  <Route path="/analytics" element={<Analytics />} />
                  <Route path="/settings" element={<Settings />} />
                </Routes>
              </Container>
            </Box>
          </Box>
        </Box>
      </SocketProvider>
    </ThemeProvider>
  );
}

export default App;
