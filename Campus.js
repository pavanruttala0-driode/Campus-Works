// models/Project.js
const mongoose = require('mongoose');

const projectSchema = new mongoose.Schema({
  title: {
    type: String,
    required: true,
    trim: true
  },
  studentName: {
    type: String,
    required: true
  },
  description: {
    type: String,
    required: true
  },
  techStack: {
    type: [String], // Array of strings (e.g., ["React", "Node.js"])
    required: true
  },
  isVerified: {
    type: Boolean,
    default: false // All new submissions start as unverified
  },
  githubUrl: {
    type: String,
    required: true
  },
  liveUrl: {
    type: String,
    default: null // Not all projects will have a live demo
  }
}, { timestamps: true }); // Automatically adds createdAt and updatedAt fields

module.exports = mongoose.model('Project', projectSchema);

