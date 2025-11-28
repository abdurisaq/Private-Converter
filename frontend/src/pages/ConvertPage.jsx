import { useState, useEffect } from 'react';
import { Upload, FileUp, AlertCircle } from 'lucide-react';
import { conversionApi } from '../utils/api';
import toast from 'react-hot-toast';

export default function ConvertPage() {
  const [file, setFile] = useState(null);
  const [inputFormat, setInputFormat] = useState('');
  const [outputFormat, setOutputFormat] = useState('');
  const [formats, setFormats] = useState({});
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchFormats();
  }, []);

  const fetchFormats = async () => {
    try {
      setLoading(true);
      const response = await conversionApi.getFormats();
      setFormats(response);
      setCategories(Object.keys(response));
      if (Object.keys(response).length > 0) {
        setSelectedCategory(Object.keys(response)[0]);
      }
    } catch (error) {
      toast.error('Failed to load formats');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      const ext = selectedFile.name.split('.').pop().toLowerCase();
      setInputFormat(ext);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      setFile(droppedFile);
      const ext = droppedFile.name.split('.').pop().toLowerCase();
      setInputFormat(ext);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return toast.error('Please select a file');
    if (!inputFormat) return toast.error('Please specify input format');
    if (!outputFormat) return toast.error('Please specify output format');

    setUploading(true);
    try {
      const response = await conversionApi.upload(file, inputFormat, outputFormat);
      const { jobId } = response.data;
      toast.success('File uploaded! Check your jobs page for status.');

      setFile(null);
      setInputFormat('');
      setOutputFormat('');
      document.getElementById('fileInput').value = '';
    } catch (error) {
      const message = error.response?.data?.error || 'Upload failed';
      toast.error(message);
    } finally {
      setUploading(false);
    }
  };

  const inputFormats = formats?.[selectedCategory]?.input || [];
  const outputFormats = formats?.[selectedCategory]?.output || [];

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="p-8 bg-gray-800 rounded-lg shadow text-center text-gray-300">
          Loading supported formats...
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-purple-400">Convert Files</h1>
        <p className="text-gray-400 mt-2">Upload a file and select your desired output format</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Category Selection */}
        <div className="p-6 bg-gray-800 rounded-lg shadow">
          <h2 className="text-lg font-semibold text-gray-100 mb-4">Conversion Type</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {categories.map((category) => (
              <button
                key={category}
                type="button"
                onClick={() => setSelectedCategory(category)}
                className={`p-3 rounded-lg border-2 text-sm font-medium transition-colors w-full ${
                  selectedCategory === category
                    ? 'border-purple-500 bg-purple-700 text-gray-100'
                    : 'border-gray-700 bg-gray-900 text-gray-300 hover:border-purple-500 hover:bg-gray-700'
                }`}
              >
                {category.charAt(0).toUpperCase() + category.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* File Upload */}
        <div className="p-6 bg-gray-800 rounded-lg shadow">
          <h2 className="text-lg font-semibold text-gray-100 mb-4">Select File</h2>
          <div
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            className="border-2 border-dashed border-gray-700 rounded-lg p-8 text-center hover:border-purple-500 transition-colors cursor-pointer"
          >
            <input
              id="fileInput"
              type="file"
              onChange={handleFileChange}
              className="hidden"
              disabled={uploading}
            />
            <label htmlFor="fileInput" className="cursor-pointer">
              <Upload className="mx-auto mb-3 text-purple-400" size={32} />
              <p className="text-gray-300 font-medium">
                {file ? file.name : 'Drag and drop your file here or click to browse'}
              </p>
              <p className="text-gray-500 text-sm mt-1">Max file size: 1GB</p>
            </label>
          </div>

          {file && (
            <div className="mt-4 p-4 bg-green-700/20 rounded-lg border border-green-500">
              <p className="text-sm text-green-400">
                <FileUp className="inline mr-2" size={16} />
                {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
              </p>
            </div>
          )}
        </div>

        {/* Format Selection */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Input Format */}
          <div className="p-6 bg-gray-800 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-100 mb-4">From Format</h2>
            <select
              value={inputFormat}
              onChange={(e) => setInputFormat(e.target.value)}
              className="w-full p-2 rounded bg-gray-900 text-gray-300 border border-gray-700"
              disabled={uploading}
            >
              <option value="">Select input format</option>
              {inputFormats.map((fmt) => (
                <option key={fmt} value={fmt}>
                  {fmt.toUpperCase()}
                </option>
              ))}
            </select>
            {inputFormat && !inputFormats.includes(inputFormat.toLowerCase()) && (
              <div className="mt-3 p-3 bg-yellow-700/20 rounded border border-yellow-500 flex gap-2">
                <AlertCircle size={16} className="text-yellow-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-yellow-300">
                  Format may not be in selected category
                </p>
              </div>
            )}
          </div>

          {/* Output Format */}
          <div className="p-6 bg-gray-800 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-100 mb-4">To Format</h2>
            <select
              value={outputFormat}
              onChange={(e) => setOutputFormat(e.target.value)}
              className="w-full p-2 rounded bg-gray-900 text-gray-300 border border-gray-700"
              disabled={uploading}
            >
              <option value="">Select output format</option>
              {outputFormats.map((fmt) => (
                <option key={fmt} value={fmt}>
                  {fmt.toUpperCase()}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={uploading || !file || !inputFormat || !outputFormat}
          className="w-full flex items-center justify-center gap-2 p-3 font-semibold text-gray-100 rounded-lg bg-purple-700 hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {uploading ? (
            <>
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <FileUp size={20} />
              Convert File
            </>
          )}
        </button>
      </form>

      {/* Info Box */}
      <div className="mt-8 p-6 bg-gray-800 rounded-lg shadow border border-gray-700">
        <h3 className="font-semibold text-gray-100 mb-2">How it works</h3>
        <ol className="text-sm text-gray-400 space-y-1 list-decimal list-inside">
          <li>Select the conversion type (audio, video, image, etc.)</li>
          <li>Upload your file by dragging or clicking</li>
          <li>Choose the output format</li>
          <li>Click "Convert File" to start</li>
          <li>Check your jobs page to download the result</li>
        </ol>
      </div>
    </div>
  );
}
