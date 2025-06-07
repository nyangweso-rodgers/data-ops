# Optical Character Recognition (OCR)

## Table Of Contents

# Optical character recognition (OCR)

# What is OCR?

- **OCR** takes images that include textual elements and attempts to recognize that text. The output is a **text string**, and accuracy is measured as the degree of similarity between the recognized text and the text a human would be able to read from the image.
- **OCR Use Cases**:

  1. **Parking validation** — Cities and towns are using mobile OCR to automatically validate if cars are parked according to city regulations. Parking inspectors can use a mobile device with OCR to scan license plates of vehicles and check with an online database to see if they are permitted to park.
  2. **Mobile document scanning** — A variety of mobile applications allow users to take a photo of a document and convert it to text. This OCR task is more challenging than traditional document scanners, because photos have unpredictable image angles, lighting conditions, and text quality.
  3. **Digital asset management** (**DAM**) — **DAM** software helps organize rich media assets such as images, videos, and animations. A key aspect of **DAM** systems is search-ability of rich media. By running OCR on uploaded images and video frames, DAM can make rich media searchable, and enrich it with meaningful tags.

- OCR Engines
  1. Tesseract
     - [Tesseract](https://github.com/tesseract-ocr/tesseract) is an open-source OCR engine developed by HP that recognizes more than 100 languages, along with the support of ideographic and right-to-left languages. Also, we can train Tesseract to recognize other languages.

# Optical Character Recognition (OCR) APIs

1. [Amazon Textract](https://docs.aws.amazon.com/managedservices/latest/userguide/textract.html)
2. [Google Cloud OCR API](https://cloud.google.com/vision/docs/ocr)
3. [Taggun](https://www.taggun.io/)
4. [Abbyy](https://www.abbyy.com/)
5. [Hive’s Optical Character Recognition API](https://thehive.ai/apis/ocr)
6. [Klippa OCR API](https://www.klippa.com/en/home-en/)

# Amazon Textract

- [Amazon Textract](https://aws.amazon.com/textract/) is a fully-managed machine learning service that enables its web service customers to automate large scale document workflows by processing millions of pages in a matter of hours. With **Textract**, users can extract structured information from many file formats with no machine learning knowledge.
- Amazon Textract **Features**:

  1. **Automating Forms Input**

     - In traditional **OCR**, without hard coding bounding boxes or implementing complex logic, it isn’t possible to retain relationships between the parts of text extracted from a given document.
     - **Textract** understands forms and extracts text blocks, maintaining relationships between them. On an image of the form, **Textract** will output a key-value pair with these attributes as key and appropriate values against each of them.

  2. **Converting Tables**

     - When extracting text from images of documents, **Textract** automatically detects tables and keeps the composition of data represented in those tables intact. The output of such data is in tabular format, which allows the user to store them easily in their databases. This is helpful for documents that are largely composed of structured data—such as financial reports or medical records—that have column names in the top row of the table followed by rows of individual entries.

  3. **Keep Reading Format Intact — Multi-Column**

     - Consider an example of extracting news from old-age newspapers, where for more readability, text was presented in a multi-column format. Textract provides a bounding box and geometry around text blocks that allow users to place the extracted text in the desired manner

  4. **Quality Assurance — Confidence Controls**
     - **Textract** outputs the text blocks extracted with a **confidence level**. This allows users to make informed decisions about how they want to use the results. Users can set the level where human intervention is required for correction or verification, depending upon the requirements.

- **Amazon Textract** has five different APIs:

  1. **Detect Document Text API**

     - uses **OCR** technology to extract text and handwriting from a document.

  2. **Analyze Document API**:

     - Has four features:

       1. **Forms**

          - extracts data such as key-value pairs (“First Name” and associated value, such as “Jane Smith”). It also uses OCR technology to extract all the text and handwriting from a document.

       2. **Tables**

          - extracts tabular or table data organized in columns and rows. It also uses OCR technology to extract all the text and handwriting from a document.

       3. **Queries**

          - provides you the flexibility to specify the information you need from a document (e.g., “What is the customer name?”) and receive that data (e.g., “Jane Doe”) as part of the response. You do not need to worry about the structure of the data in the document or variations in how the data is laid out across different formats and versions of the document.
          - It also uses OCR technology to extract all the text and handwriting from a document.

       4. **Signatures**: provides the ability to detect handwritten signatures, electronic signatures, and initials on any document or image. It also uses OCR technology to extract all the text and handwriting from a document.

     - You have the flexibility to call any combination of **Forms**, **Tables**, **Queries**, and **Signatures** together.
     - Analyze Document API for **Forms**

  3. **Analyze Expense API**

  4. **Analyze ID API**

     - **Analyze ID API** uses ML to understand the context of identity documents such as U.S. passports, driver’s licenses, and other IDs. You can automatically extract specific information such as date of expiry and date of birth, as well as intelligently identify and extract implied information such as name and address. Each ID image is considered a page.

  5. **Analyze Lending API**
     - **Analyze Lending API** is a specialized mortgage document processing API that automates the classification and extraction of information from a range of mortgage-related application documents. Analyze Lending’s machine learning models have been pre-trained across the diversity of document types that are seen in a typical mortgage application package. Analyze Lending will classify, split and extract results with accuracy and provide a summary of your results including whether or not a signature was detected on the page.

# Google Cloud Vision API

# References and Further Reading

1. [Google Clocud - Cloud Vision API](https://cloud.google.com/vision/docs/reference/rest/?apix=true)
