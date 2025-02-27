import { useState, useRef, useEffect } from 'react';
import styles from '../../styles/Home.module.css';

interface JobFormProps {
  onSubmit: (formData: JobFormData) => void;
}

export interface JobFormData {
  companyName: string;
  companyDescription: string;
  jobDescription: string;
  calComLink: string;
  contactEmail: string;
}

export default function JobForm({ onSubmit }: JobFormProps) {
  const [formData, setFormData] = useState<JobFormData>({
    companyName: '',
    companyDescription: '',
    jobDescription: '',
    calComLink: '',
    contactEmail: ''
  });
  
  const formRef = useRef<HTMLFormElement>(null);
  const companyDescriptionRef = useRef<HTMLTextAreaElement>(null);
  const jobDescriptionRef = useRef<HTMLTextAreaElement>(null);

  const autoResizeTextarea = (textarea: HTMLTextAreaElement | null) => {
    if (!textarea) return;
    
    // Reset height to auto first to get the correct scrollHeight
    textarea.style.height = 'auto';
    
    // Calculate new height (min of scrollHeight or max height of 200px)
    const newHeight = Math.min(textarea.scrollHeight, 200);
    
    // Set the height
    textarea.style.height = `${newHeight}px`;
  };

  useEffect(() => {
    // Auto-resize textareas on mount
    autoResizeTextarea(companyDescriptionRef.current);
    autoResizeTextarea(jobDescriptionRef.current);
    
    // Remove the scroll into view logic from here since it's handled in the parent
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Auto-resize if it's a textarea
    if (e.target.tagName.toLowerCase() === 'textarea') {
      autoResizeTextarea(e.target as HTMLTextAreaElement);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form ref={formRef} onSubmit={handleSubmit} className={styles.jobForm}>
      <div className={styles.formField}>
        <label htmlFor="companyName">Company Name</label>
        <input
          type="text"
          id="companyName"
          name="companyName"
          value={formData.companyName}
          onChange={handleChange}
          required
          className={styles.jobFormInput}
          placeholder="Enter your company name"
        />
      </div>

      <div className={styles.formField}>
        <label htmlFor="companyDescription">Company Description</label>
        <textarea
          ref={companyDescriptionRef}
          id="companyDescription"
          name="companyDescription"
          value={formData.companyDescription}
          onChange={handleChange}
          required
          className={styles.jobFormTextarea}
          placeholder="Brief description of your company"
          rows={3}
        />
      </div>

      <div className={styles.formField}>
        <label htmlFor="jobDescription">Job Description</label>
        <textarea
          ref={jobDescriptionRef}
          id="jobDescription"
          name="jobDescription"
          value={formData.jobDescription}
          onChange={handleChange}
          required
          className={styles.jobFormTextarea}
          placeholder="Detailed description of the job position"
          rows={5}
        />
      </div>

      <div className={styles.formField}>
        <label htmlFor="calComLink">Cal.com Link</label>
        <input
          type="url"
          id="calComLink"
          name="calComLink"
          value={formData.calComLink}
          onChange={handleChange}
          required
          className={styles.jobFormInput}
          placeholder="Your Cal.com booking link"
        />
      </div>

      <div className={styles.formField}>
        <label htmlFor="contactEmail">Contact Email</label>
        <input
          type="email"
          id="contactEmail"
          name="contactEmail"
          value={formData.contactEmail}
          onChange={handleChange}
          required
          className={styles.jobFormInput}
          placeholder="Your email address"
        />
      </div>

      <button type="submit" className={`${styles.sendButton} ${styles.sendButtonEnabled}`}>
        Submit Job
      </button>
    </form>
  );
} 