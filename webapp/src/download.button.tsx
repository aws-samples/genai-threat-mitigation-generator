import Button from '@cloudscape-design/components/button';
import JsPDF from 'jspdf';

interface Props {
  filename: string
  value: string
  disabled?: boolean
}

export const DownloadButton = ({ value, filename, disabled }: Props) => {
  return <>
    <Button
      variant="normal"
      disabled={ disabled }
      onClick={ (event) => {
        event.preventDefault()
        const blob = new Blob([ value ], { type: 'text/plain' });
        const link = window.document.createElement('a');
        const href = window.URL.createObjectURL(blob);
        link.href = href
        link.download = `${ filename }.txt`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(href)
      } }
    >Download as text</Button>
    <Button
      variant="normal"
      disabled={ disabled }
      onClick={ (event) => {
      event.preventDefault()
      const doc = new JsPDF({})
      const pageHeight = doc.internal.pageSize.height;
      const wrappedText = doc.splitTextToSize(value, 180);
      doc.setFontSize(14);
      let iterations = 1; // we need control the iterations of line
      const margin = 15; //top and botton margin in mm
      const defaultYJump = 5; // default space btw lines

      wrappedText.forEach((line) => {
        let posY = margin + defaultYJump * iterations++;
        if (posY > pageHeight - margin) {
          doc.addPage();
          iterations = 1;
          posY = margin + defaultYJump * iterations++;
        }
        doc.text(line, margin, posY);
      });
      doc.save(`${ filename }.pdf`); // will save the file in the current working directory
    } }>
      Download as PDF
    </Button>
  </>
}