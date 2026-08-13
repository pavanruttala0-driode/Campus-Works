import React from 'react';

const ProjectCard = ({ project }) => {
  // Destructure the project data for cleaner code
  const { 
    title, 
    studentName, 
    description, 
    techStack, 
    isVerified, 
    githubUrl, 
    liveUrl 
  } = project;

  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-shadow duration-300 overflow-hidden flex flex-col h-full">
      
      <div className="p-5 flex-grow">
        {/* Header: Title and Verification Badge */}
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-xl font-bold text-gray-900">{title}</h3>
          {isVerified && (
            <span className="inline-flex items-center gap-1 bg-green-50 text-green-700 text-xs font-semibold px-2.5 py-1 rounded-full border border-green-200">
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              Verified
            </span>
          )}
        </div>

        {/* Student Name */}
        <p className="text-sm font-medium text-gray-500 mb-3">
          Built by {studentName}
        </p>

        {/* Project Description */}
        <p className="text-gray-600 text-sm mb-4 line-clamp-3">
          {description}
        </p>

        {/* Tech Stack Chips */}
        <div className="flex flex-wrap gap-2 mb-4">
          {techStack.map((tech, index) => (
            <span 
              key={index} 
              className="bg-blue-50 text-blue-700 text-xs px-2 py-1 rounded-md border border-blue-100"
            >
              {tech}
            </span>
          ))}
        </div>
      </div>

      {/* Footer: Action Links */}
      <div className="bg-gray-50 border-t border-gray-100 p-4 flex gap-3 mt-auto">
        {liveUrl && (
          <a 
            href={liveUrl} 
            target="_blank" 
            rel="noopener noreferrer"
            className="flex-1 text-center bg-black text-white text-sm font-medium py-2 rounded-lg hover:bg-gray-800 transition-colors"
          >
            Live Demo
          </a>
        )}
        {githubUrl && (
          <a 
            href={githubUrl} 
            target="_blank" 
            rel="noopener noreferrer"
            className="flex-1 text-center bg-white text-gray-700 text-sm font-medium py-2 rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors"
          >
            View Code
          </a>
        )}
      </div>
      
    </div>
  );
};

export default ProjectCard;
