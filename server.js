// server.js
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
require('dotenv').config();

const projectRoutes = require('./routes/projectRoutes');

const app = express();

// Middleware
app.use(cors()); // Allows your React app to make requests here
app.use(express.json()); // Parses incoming JSON data

// Routes
app.use('/api/projects', projectRoutes);

// Database Connection
// For now, we will use a local MongoDB URI, but you can replace this with MongoDB Atlas later
const PORT = process.env.PORT || 5000;
const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017/campus-works';

mongoose.connect(MONGO_URI)
  .then(() => {
    console.log('✅ Connected to MongoDB');
    app.listen(PORT, () => {
      console.log(`🚀 Server running on http://localhost:${PORT}`);
    });
  })
  .catch((error) => {
    console.error('❌ Database connection failed:', error);
  });
