// routes/projectRoutes.js
const express = require('express');
const router = express.Router();
const Project = require('../models/Project');

// GET: Fetch all verified projects for the Discovery Hub
router.get('/', async (req, res) => {
  try {
    // Only return projects that have been approved by a professor
    const projects = await Project.find({ isVerified: true }).sort({ createdAt: -1 });
    res.json(projects);
  } catch (error) {
    res.status(500).json({ message: 'Server error fetching projects' });
  }
});

// POST: Submit a new project (Student action)
router.post('/', async (req, res) => {
  try {
    const { title, studentName, description, techStack, githubUrl, liveUrl } = req.body;
    
    const newProject = new Project({
      title,
      studentName,
      description,
      techStack,
      githubUrl,
      liveUrl
      // isVerified defaults to false automatically
    });

    const savedProject = await newProject.save();
    res.status(201).json(savedProject);
  } catch (error) {
    res.status(400).json({ message: 'Failed to submit project', error: error.message });
  }
});

module.exports = router;
