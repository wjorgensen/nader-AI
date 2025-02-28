import { JobFormData } from '../src/pages/components/JobForm';

/**
 * Submits a job to the server
 * @param jobData The job data from the form
 * @returns The server response with the created job
 */
export async function submitJob(jobData: JobFormData) {
  try {
    const baseUrl = process.env.DB_BASE_URL || 'http://localhost:8000';
    const response = await fetch(`${baseUrl}/api/jobs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(jobData),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: `Error: ${response.status} ${response.statusText}` }));
      throw new Error(errorData?.detail || `Error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to submit job:', error);
    throw error;
  }
}

