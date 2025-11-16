import { Document, Packer, Paragraph, TextRun, HeadingLevel } from 'docx';
import type { Meeting } from '../features/dashboard/Dashboard';

export async function exportToWord(meeting: Meeting) {
  const doc = new Document({
    sections: [{
      properties: {},
      children: [
        // Title
        new Paragraph({
          text: meeting.title,
          heading: HeadingLevel.HEADING_1,
          spacing: { after: 200 }
        }),

        // Date
        new Paragraph({
          children: [
            new TextRun({
              text: `Date: ${meeting.date}`,
              color: "666666",
              size: 20
            })
          ],
          spacing: { after: 400 }
        }),

        // Summary Header
        new Paragraph({
          text: "Summary",
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 200, after: 100 }
        }),

        // Summary Content
        ...meeting.summary.split('\n').map(line => 
          new Paragraph({
            text: line || ' ',
            spacing: { after: 100 }
          })
        ),

        // Content Header
        new Paragraph({
          text: "Meeting Content",
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 400, after: 100 }
        }),

        // Content
        ...meeting.content.split('\n').map(line => 
          new Paragraph({
            text: line || ' ',
            spacing: { after: 100 }
          })
        ),

        // Action Items Header
        ...(meeting.actionItems.length > 0 ? [
          new Paragraph({
            text: "Action Items",
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 400, after: 200 }
          })
        ] : []),

        // Action Items List
        ...meeting.actionItems.flatMap((item, index) => [
          new Paragraph({
            children: [
              new TextRun({
                text: `${index + 1}. `,
                bold: true
              }),
              new TextRun({
                text: item.completed ? '☑ ' : '☐ ',
                size: 24
              }),
              new TextRun({
                text: item.text,
                strike: item.completed
              })
            ],
            spacing: { after: 100 }
          }),
          ...(item.assignee ? [
            new Paragraph({
              children: [
                new TextRun({
                  text: `   Assignee: ${item.assignee}`,
                  color: "666666",
                  size: 20
                })
              ],
              spacing: { after: 50 }
            })
          ] : []),
          ...(item.dueDate ? [
            new Paragraph({
              children: [
                new TextRun({
                  text: `   Due Date: ${item.dueDate}`,
                  color: "666666",
                  size: 20
                })
              ],
              spacing: { after: 150 }
            })
          ] : [new Paragraph({ text: '', spacing: { after: 150 } })])
        ])
      ]
    }]
  });

  // Generate and download the document
  const blob = await Packer.toBlob(doc);
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  const fileName = `${meeting.title.replace(/[^a-z0-9]/gi, '_')}_${meeting.date}.docx`;
  link.download = fileName;
  link.click();
  window.URL.revokeObjectURL(url);
}
