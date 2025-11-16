import { jsPDF } from 'jspdf';
import type { Meeting } from '../features/dashboard/Dashboard';

// Add Korean font support (using default font with Unicode support)
export function exportToPDF(meeting: Meeting) {
  const doc = new jsPDF();
  
  let yPosition = 20;
  const lineHeight = 7;
  const pageHeight = doc.internal.pageSize.height;
  const margin = 20;

  // Helper function to add text with automatic page breaks
  const addText = (text: string, fontSize = 12, isBold = false) => {
    doc.setFontSize(fontSize);
    
    // Split text by newlines first
    const lines = text.split('\n');
    
    lines.forEach(line => {
      // Split long lines to fit page width
      const splitLines = doc.splitTextToSize(line || ' ', 170);
      
      splitLines.forEach((splitLine: string) => {
        if (yPosition > pageHeight - margin) {
          doc.addPage();
          yPosition = 20;
        }
        
        doc.text(splitLine, 20, yPosition);
        yPosition += lineHeight;
      });
    });
  };

  // Title
  doc.setFontSize(18);
  doc.text(meeting.title, 20, yPosition);
  yPosition += 10;

  // Date
  doc.setFontSize(10);
  doc.setTextColor(100);
  doc.text(`Date: ${meeting.date}`, 20, yPosition);
  yPosition += 10;
  doc.setTextColor(0);

  // Summary section
  doc.setFontSize(14);
  doc.text('Summary', 20, yPosition);
  yPosition += 8;
  
  doc.setFontSize(11);
  addText(meeting.summary, 11);
  yPosition += 5;

  // Content section
  doc.setFontSize(14);
  doc.text('Meeting Content', 20, yPosition);
  yPosition += 8;
  
  doc.setFontSize(11);
  addText(meeting.content, 11);
  yPosition += 5;

  // Action Items section
  if (meeting.actionItems.length > 0) {
    if (yPosition > pageHeight - 60) {
      doc.addPage();
      yPosition = 20;
    }

    doc.setFontSize(14);
    doc.text('Action Items', 20, yPosition);
    yPosition += 8;

    meeting.actionItems.forEach((item, index) => {
      if (yPosition > pageHeight - 40) {
        doc.addPage();
        yPosition = 20;
      }

      doc.setFontSize(11);
      const status = item.completed ? '[X]' : '[ ]';
      doc.text(`${index + 1}. ${status} ${item.text}`, 25, yPosition);
      yPosition += 6;

      doc.setFontSize(9);
      doc.setTextColor(100);
      if (item.assignee) {
        doc.text(`   Assignee: ${item.assignee}`, 30, yPosition);
        yPosition += 5;
      }
      if (item.dueDate) {
        doc.text(`   Due Date: ${item.dueDate}`, 30, yPosition);
        yPosition += 5;
      }
      doc.setTextColor(0);
      yPosition += 3;
    });
  }

  // Save the PDF
  const fileName = `${meeting.title.replace(/[^a-z0-9]/gi, '_')}_${meeting.date}.pdf`;
  doc.save(fileName);
}
