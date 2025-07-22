import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Plus, Trash2, ChevronDown, Image as ImageIcon, UploadCloud } from 'lucide-react';
import api from '../services/api';

const InputField = ({ label, name, id, value, onChange, type = 'text', placeholder = '', required = false, span = 'col-span-1' }) => (
    <div className={span}>
        <label htmlFor={id} className="block mb-2 text-sm font-medium text-gray-300">{label}</label>
        <input type={type} id={id} name={name} value={value} onChange={onChange} placeholder={placeholder} required={required} className="w-full px-3 py-2 text-white bg-gray-700 border border-gray-600 rounded-lg focus:ring-yellow-500 focus:border-yellow-500" />
    </div>
);

const SelectField = ({ label, name, id, value, onChange, children, span = 'col-span-1' }) => (
    <div className={span}>
        <label htmlFor={id} className="block mb-2 text-sm font-medium text-gray-300">{label}</label>
        <select id={id} name={name} value={value} onChange={onChange} className="w-full px-3 py-2 text-white bg-gray-700 border border-gray-600 rounded-lg focus:ring-yellow-500 focus:border-yellow-500">{children}</select>
    </div>
);

const ImageUploadField = ({ label, id, required, onImageChange }) => {
    const [preview, setPreview] = useState(null);
    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            const previewUrl = URL.createObjectURL(file);
            setPreview(previewUrl);
            onImageChange(file);
        } else {
            setPreview(null);
            onImageChange(null);
        }
    };
    useEffect(() => { return () => { if (preview) URL.revokeObjectURL(preview); }; }, [preview]);
    return (
        <div className="w-full">
            <label htmlFor={id} className="block mb-2 text-sm font-medium text-gray-300">{label}{required && <span className="text-red-500">*</span>}</label>
            <div className="flex items-center gap-4 p-4 bg-black/20 rounded-lg">
                <input id={id} type="file" accept="image/*" onChange={handleFileChange} className="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-yellow-500/20 file:text-yellow-300 hover:file:bg-yellow-500/30" />
                {preview ? <img src={preview} alt="Preview" className="h-16 w-16 object-cover rounded-lg border border-gray-600" /> : <div className="h-16 w-16 flex-shrink-0 flex items-center justify-center bg-gray-700 rounded-lg border border-gray-600"><ImageIcon className="text-gray-500" /></div>}
            </div>
        </div>
    );
};

const VariationForm = ({ variacao, productSku, index, handleVariationChange, removeVariation }) => {
    const generateSku = () => {
        const parentSku = productSku || "PRODUTO";
        const newSku = `${parentSku}-VAR${index + 1}-${Date.now().toString().slice(-4)}`;
        const fakeEvent = { target: { name: 'sku', value: newSku } };
        handleVariationChange(variacao.id, fakeEvent);
    };
    return (
        <div className="p-4 border border-gray-700 rounded-lg space-y-4 relative">
            <div className="absolute top-2 right-2"><button type="button" onClick={() => removeVariation(variacao.id)} className="p-1 text-red-400 hover:text-red-200"><Trash2 size={16} /></button></div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="md:col-span-2"><InputField label={`SKU da Variação ${index + 1}`} name="sku" id={`var-sku-${variacao.id}`} value={variacao.sku} onChange={(e) => handleVariationChange(variacao.id, e)} /></div>
                <div className="flex items-end"><button type="button" onClick={generateSku} className="w-full h-10 px-4 text-sm font-bold text-black bg-yellow-400/80 rounded-lg hover:bg-yellow-500">Gerar SKU</button></div>
            </div>
            <SelectField label="Tipo de Variação" name="tipo" id={`var-tipo-${variacao.id}`} value={variacao.tipo} onChange={(e) => handleVariationChange(variacao.id, e)}><option value="">Selecione o tipo...</option><option value="cor">Cor</option><option value="c_l_a_p">Tamanho e Peso</option></SelectField>
            {variacao.tipo === 'cor' && (<InputField label="Nome da Cor" name="cor" id={`var-cor-${variacao.id}`} value={variacao.cor} onChange={(e) => handleVariationChange(variacao.id, e)} />)}
            {variacao.tipo === 'c_l_a_p' && (<div className="grid grid-cols-1 md:grid-cols-2 gap-4"><InputField label="Dimensões (C x L x A)" name="cla" id={`var-cla-${variacao.id}`} value={variacao.cla} onChange={(e) => handleVariationChange(variacao.id, e)} placeholder="ex: 18x13x8" /><InputField label="Peso do Produto (g)" name="peso" id={`var-peso-${variacao.id}`} value={variacao.peso} onChange={(e) => handleVariationChange(variacao.id, e)} type="number" /></div>)}
            <InputField label="URL Imagem Principal da Variação" name="imagem" id={`var-img-${variacao.id}`} value={variacao.imagem} onChange={(e) => handleVariationChange(variacao.id, e)} />
        </div>
    );
};

const ProductForm = ({ product, index, removeProduct, handleProductChange, handleVariationChange, addVariation, removeVariation, handleImageChange, addExtraImage, removeExtraImage, handleExtraImageChange }) => {
    const [isExpanded, setIsExpanded] = useState(true);
    const toggleExpansion = () => setIsExpanded(!isExpanded);
    const handleRemoveClick = (e) => { e.stopPropagation(); removeProduct(product.id); };
    const showNomeMarca = product.tipo_marca === 'Marca';
    const showNcm = product.fba_dba === 'FBA';
    const showQuantidade = product.fba_dba === 'FBA';
    const showTipoId = product.id_produto !== '';
    return (
        <div className="p-6 mt-4 bg-gray-800/50 rounded-lg border border-yellow-500/20 transition-all duration-300">
            <div className="flex justify-between items-center cursor-pointer" onClick={toggleExpansion}>
                <h2 className="text-xl font-semibold text-white">Listagem - {product.titulo || `Produto ${index + 1}`}</h2>
                <div className="flex items-center gap-3"><ChevronDown size={24} className={`text-white transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`} /><button onClick={handleRemoveClick} className="p-2 text-red-400 hover:text-red-200 hover:bg-red-500/20 rounded-full transition-colors" aria-label="Remover Produto"><Trash2 size={20} /></button></div>
            </div>
            <div className={`transition-all duration-500 ease-in-out overflow-hidden ${isExpanded ? 'max-h-[5000px] pt-4' : 'max-h-0'}`}>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <InputField label="Título do Produto" name="titulo" id={`titulo-${product.id}`} value={product.titulo} onChange={(e) => handleProductChange(product.id, e)} required span="md:col-span-3" />
                    <InputField label="SKU" name="sku" id={`sku-${product.id}`} value={product.sku} onChange={(e) => handleProductChange(product.id, e)} />
                    <SelectField label="Tipo de Marca" name="tipo_marca" id={`tipo_marca-${product.id}`} value={product.tipo_marca} onChange={(e) => handleProductChange(product.id, e)}><option value="">Selecione...</option><option value="Genérico">Genérico</option><option value="Marca">Marca</option></SelectField>
                    {showNomeMarca && <InputField label="Nome da Marca" name="nome_marca" id={`nome_marca-${product.id}`} value={product.nome_marca} onChange={(e) => handleProductChange(product.id, e)} />}
                    <InputField label="Preço" name="preco" id={`preco-${product.id}`} value={product.preco} onChange={(e) => handleProductChange(product.id, e)} type="number" />
                    <SelectField label="FBA ou DBA" name="fba_dba" id={`fba_dba-${product.id}`} value={product.fba_dba} onChange={(e) => handleProductChange(product.id, e)}><option value="">Selecione...</option><option value="FBA">FBA</option><option value="DBA">DBA</option></SelectField>
                    <InputField label="ID do produto" name="id_produto" id={`id_produto-${product.id}`} value={product.id_produto} onChange={(e) => handleProductChange(product.id, e)} />
                    {showTipoId && (<SelectField label="Tipo de ID do Produto" name="tipo_id_produto" id={`tipo_id_produto-${product.id}`} value={product.tipo_id_produto} onChange={(e) => handleProductChange(product.id, e)}><option value="">Selecione...</option><option value="EAN">EAN</option><option value="GTIN">GTIN</option><option value="UPC">UPC</option></SelectField>)}
                    {showNcm && <InputField label="NCM" name="ncm" id={`ncm-${product.id}`} value={product.ncm} onChange={(e) => handleProductChange(product.id, e)} />}
                    {showQuantidade && <InputField label="Quantidade de Estoque" name="quantidade" id={`quantidade-${product.id}`} value={product.quantidade} onChange={(e) => handleProductChange(product.id, e)} type="number" />}
                    <InputField label="Peso do Pacote (g)" name="peso_pacote" id={`peso_pacote-${product.id}`} value={product.peso_pacote} onChange={(e) => handleProductChange(product.id, e)} type="number" span="md:col-span-2" />
                    <InputField label="Dimensões (pacote) C x L x A" name="c_l_a_pacote" id={`c_l_a_pacote-${product.id}`} value={product.c_l_a_pacote} onChange={(e) => handleProductChange(product.id, e)} placeholder="ex: 20x15x10" span="md:col-span-2" />
                    <InputField label="Peso do Produto (g)" name="peso_produto" id={`peso_produto-${product.id}`} value={product.peso_produto} onChange={(e) => handleProductChange(product.id, e)} type="number" span="md:col-span-2" />
                    <InputField label="Dimensões (produto) C x L x A" name="c_l_a_produto" id={`c_l_a_produto-${product.id}`} value={product.c_l_a_produto} onChange={(e) => handleProductChange(product.id, e)} placeholder="ex: 18x13x8" span="md:col-span-2" />
                    <SelectField label="O Produto é Ajustável?" name="ajuste" id={`ajuste-${product.id}`} value={product.ajuste} onChange={(e) => handleProductChange(product.id, e)} span="md:col-span-2"><option value="">Selecione...</option><option value="NÃO">Não</option><option value="SIM">Sim</option></SelectField>
                    <div className="md:col-span-4 mt-4 border-t border-yellow-500/20 pt-4">
                        <div className="flex justify-between items-center mb-4"><h3 className="text-lg font-semibold text-yellow-400">Variações do Produto</h3><button type="button" onClick={() => addVariation(product.id)} className="flex items-center gap-2 px-3 py-1.5 text-xs font-bold text-black bg-yellow-400 rounded-lg hover:bg-yellow-500"><Plus size={16} />Adicionar Variação</button></div>
                        <div className="space-y-4">{product.variacoes.map((variacao, varIndex) => (<VariationForm key={variacao.id} variacao={variacao} productSku={product.sku} index={varIndex} handleVariationChange={(variationId, e) => handleVariationChange(product.id, variationId, e)} removeVariation={() => removeVariation(product.id, variacao.id)} />))}</div>
                    </div>
                    <div className="md:col-span-4 mt-4 border-t border-yellow-500/20 pt-4 space-y-4">
                        <h3 className="text-lg font-semibold text-yellow-400">Imagens do Produto</h3>
                        <ImageUploadField label="Imagem Principal" id={`img-principal-${product.id}`} required onImageChange={(file) => handleImageChange(product.id, 'principal', file)} />
                        <ImageUploadField label="Imagem de Amostra" id={`img-amostra-${product.id}`} required onImageChange={(file) => handleImageChange(product.id, 'amostra', file)} />
                        <div className="flex justify-between items-center mt-4"><h4 className="font-semibold text-gray-200">Imagens Adicionais</h4><button type="button" onClick={() => addExtraImage(product.id)} className="flex items-center gap-2 px-3 py-1.5 text-xs font-bold text-black bg-yellow-400 rounded-lg hover:bg-yellow-500"><Plus size={16} />Adicionar Imagem</button></div>
                        <div className="space-y-3">{product.imagens.extra.map((img, imgIndex) => (<div key={img.id} className="flex items-end gap-3"><div className="flex-grow"><ImageUploadField label={`Imagem Extra ${imgIndex + 1}`} id={`img-extra-${img.id}`} onImageChange={(file) => handleExtraImageChange(product.id, img.id, file)} /></div><button type="button" onClick={() => removeExtraImage(product.id, img.id)} className="p-2 mb-1 text-red-400 hover:text-red-200 hover:bg-red-500/20 rounded-full"><Trash2 size={18} /></button></div>))}</div>
                    </div>
                </div>
            </div>
        </div>
    )
};

const createNewVariation = () => ({ id: Date.now(), sku: '', tipo: '', cor: '', cla: '', peso: '', imagem: '' });
const createNewExtraImage = () => ({ id: Date.now(), file: null });
const createNewProduct = (initialData = {}, index = 0) => ({
    id: initialData.id || Date.now() + index,
    titulo: initialData.titulo || '', sku: initialData.sku || '', tipo_marca: initialData.tipo_marca || '', nome_marca: initialData.nome_marca || '', preco: initialData.preco || '', fba_dba: initialData.fba_dba || '',
    id_produto: initialData.id_produto || '', tipo_id_produto: initialData.tipo_id_produto || '', ncm: initialData.ncm || '', quantidade: initialData.quantidade || '', peso_pacote: initialData.peso_pacote || '',
    c_l_a_pacote: initialData.c_l_a_pacote || '', peso_produto: initialData.peso_produto || '', c_l_a_produto: initialData.c_l_a_produto || '', ajuste: initialData.ajuste || '',
    variacoes: (initialData.variacoes || []).map(v => ({...v, id: v.id || Date.now()})),
    imagens: initialData.imagens || { principal: null, amostra: null, extra: [] }
});

const downloadBase64File = (base64Data, fileName) => {
    try {
        const byteCharacters = atob(base64Data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'application/vnd.ms-excel.sheet.macroEnabled.12' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(link);
    } catch (error) {
        console.error("Erro ao tentar fazer o download do arquivo:", error);
    }
};

function CriarListing() {
    const [selectedFile, setSelectedFile] = useState(null);
    const [amazonTemplate, setAmazonTemplate] = useState(null);
    const [products, setProducts] = useState([createNewProduct()]);
    const [isLoading, setIsLoading] = useState(false);
    const [feedbackMessage, setFeedbackMessage] = useState('');
    const [pollingIntervalId, setPollingIntervalId] = useState(null);
    
    const location = useLocation();
    const navigate = useNavigate();

    useEffect(() => {
        if (location.state && location.state.products) {
            const productsFromState = location.state.products.map((p, index) => createNewProduct(p, index));
            setProducts(productsFromState);
            navigate(location.pathname, { replace: true, state: {} });
        }
    }, [location, navigate]);

    useEffect(() => {
        return () => {
            if (pollingIntervalId) {
                clearInterval(pollingIntervalId);
            }
        };
    }, [pollingIntervalId]);

    const updateProductState = (productId, updateCallback) => { setProducts(prev => prev.map(p => p.id === productId ? updateCallback(p) : p)); };
    const handleProductChange = (id, event) => { const { name, value } = event.target; updateProductState(id, p => ({ ...p, [name]: value })); };
    const addVariation = (productId) => updateProductState(productId, p => ({ ...p, variacoes: [...p.variacoes, createNewVariation()] }));
    const removeVariation = (productId, variationId) => updateProductState(productId, p => ({ ...p, variacoes: p.variacoes.filter(v => v.id !== variationId) }));
    const handleVariationChange = (productId, variationId, event) => { const { name, value } = event.target; updateProductState(productId, p => ({ ...p, variacoes: p.variacoes.map(v => v.id === variationId ? { ...v, [name]: value } : v) })); };
    const handleImageChange = (productId, imageType, file) => updateProductState(productId, p => ({ ...p, imagens: { ...p.imagens, [imageType]: file } }));
    const addExtraImage = (productId) => updateProductState(productId, p => ({ ...p, imagens: { ...p.imagens, extra: [...p.imagens.extra, createNewExtraImage()] } }));
    const removeExtraImage = (productId, imageId) => updateProductState(productId, p => ({ ...p, imagens: { ...p.imagens, extra: p.imagens.extra.filter(img => img.id !== imageId) } }));
    const handleExtraImageChange = (productId, imageId, file) => { updateProductState(productId, p => ({ ...p, imagens: { ...p.imagens, extra: p.imagens.extra.map(img => img.id === imageId ? { ...img, file: file } : img) } })); };

    const handleUploadSubmit = async () => {
        if (!selectedFile) return;
        setIsLoading(true);
        setFeedbackMessage('Enviando planilha de produtos...');
        const formData = new FormData();
        formData.append('planilha', selectedFile);
        try {
            const response = await api.post('/upload-planilha/', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
            const productsFromApi = response.data.map((p, index) => createNewProduct(p, index));
            setProducts(productsFromApi.length > 0 ? productsFromApi : [createNewProduct()]);
            setFeedbackMessage('Planilha de produtos carregada!');
        } catch (error) {
            console.error("Erro no upload da planilha de produtos:", error);
            setFeedbackMessage('Erro ao processar a planilha de produtos.');
        } finally {
            setIsLoading(false);
        }
    };

    const pollTaskStatus = (taskId) => {
        const intervalId = setInterval(async () => {
            try {
                const { data } = await api.get(`/task-status/${taskId}/`);
                if (data.status === 'SUCCESS') {
                    clearInterval(intervalId);
                    setPollingIntervalId(null);
                    const fileContent = data.result.file_content;
                    const fileName = data.result.filename;
                    downloadBase64File(fileContent, fileName);
                    setFeedbackMessage('Planilha gerada com sucesso!');
                    setIsLoading(false);
                } else if (data.status === 'FAILURE') {
                    clearInterval(intervalId);
                    setPollingIntervalId(null);
                    setIsLoading(false);
                    setFeedbackMessage('Ocorreu um erro ao gerar a planilha.');
                } else if (data.status === 'PROGRESS') {
                    const meta = data.result;
                    if (meta && meta.step) {
                        setFeedbackMessage(`${meta.step} (${meta.current || ''} de ${meta.total || ''})`);
                    }
                }
            } catch (error) {
                clearInterval(intervalId);
                setPollingIntervalId(null);
                setIsLoading(false);
                setFeedbackMessage('Erro ao consultar o estado da tarefa.');
            }
        }, 3000);
        setPollingIntervalId(intervalId);
    };

    const handleFinalSubmit = async (e) => {
        e.preventDefault();
        if (!amazonTemplate) {
            setFeedbackMessage('Por favor, envie o modelo de planilha da Amazon (.xlsm).');
            return;
        }
        setIsLoading(true);
        setFeedbackMessage('Enviando dados, imagens e template para o backend...');
        
        const formData = new FormData();
        const productsDataOnly = products.map(p => { const { imagens, ...rest } = p; return rest; });
        formData.append('products_data', JSON.stringify(productsDataOnly));
        formData.append('amazon_template', amazonTemplate);

        products.forEach((p, productIndex) => {
            if (p.imagens.principal) formData.append(`imagem_p${productIndex}_principal`, p.imagens.principal);
            if (p.imagens.amostra) formData.append(`imagem_p${productIndex}_amostra`, p.imagens.amostra);
            p.imagens.extra.forEach((img, extraIndex) => { if (img.file) formData.append(`imagem_p${productIndex}_extra_${extraIndex}`, img.file); });
        });

        try {
            const response = await api.post('/gerar-planilha/', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
            const { task_id } = response.data;
            setFeedbackMessage('Processamento iniciado! Aguardando o resultado...');
            pollTaskStatus(task_id);
        } catch (error) {
            console.error("Erro ao iniciar a geração da planilha:", error);
            setFeedbackMessage('Erro ao iniciar a geração da planilha.');
            setIsLoading(false);
        }
    };

    return (
        <div>
            {isLoading && (
                <div className="fixed top-0 left-0 w-full h-full bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-gray-800 p-6 rounded-lg shadow-xl text-center">
                        <p className="text-white text-lg">{feedbackMessage}</p>
                        <div className="w-16 h-16 border-4 border-dashed rounded-full animate-spin border-yellow-400 mx-auto mt-4"></div>
                    </div>
                </div>
            )}

            <h1 className="text-3xl font-bold uppercase text-yellow-400 mb-6">1. Envie suas planilhas</h1>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-6 bg-gray-800/50 rounded-lg border border-yellow-500/20 flex flex-col">
                    <h2 className="text-xl font-bold text-yellow-400 mb-2">Planilha de Produtos</h2>
                    <p className="text-gray-400 mb-4 flex-grow">Envie a planilha com os dados dos produtos que você quer enriquecer. A IA irá ler estas informações para preencher os formulários abaixo.</p>
                    <div className="bg-black/20 p-4 rounded-lg">
                        <label htmlFor="planilha_produtos" className="block mb-2 text-sm font-medium text-gray-300">Arquivo de Produtos (.xlsx):</label>
                        <input type="file" name="planilha_produtos" id="planilha_produtos" className="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-yellow-500/20 file:text-yellow-300 hover:file:bg-yellow-500/30" onChange={(e) => setSelectedFile(e.target.files[0])} />
                    </div>
                    <button type="button" onClick={handleUploadSubmit} className="px-6 py-2 mt-4 font-bold text-black bg-yellow-400 rounded-lg hover:bg-yellow-500 disabled:bg-gray-600 w-full" disabled={!selectedFile || isLoading}>
                        {isLoading ? 'Processando...' : 'Carregar Produtos'}
                    </button>
                </div>
                
                <div className="p-6 bg-gray-800/50 rounded-lg border border-yellow-500/20 flex flex-col">
                    <h2 className="text-xl font-bold text-yellow-400 mb-2">Modelo da Amazon</h2>
                    <p className="text-gray-400 mb-4 flex-grow">Faça o upload do seu arquivo de modelo da Amazon (.xlsm). Este arquivo será preenchido com os dados dos produtos abaixo.</p>
                     <div className="bg-black/20 p-4 rounded-lg flex flex-col items-center justify-center border-2 border-dashed border-gray-600 hover:border-yellow-500 transition-colors h-full">
                        <UploadCloud className="w-10 h-10 text-gray-500 mb-2" />
                        <label htmlFor="amazon_template_upload" className="relative cursor-pointer bg-yellow-500/20 text-yellow-300 hover:bg-yellow-500/30 font-semibold rounded-md px-3 py-2 text-sm">
                            <span>{amazonTemplate ? amazonTemplate.name : 'Selecione o arquivo de modelo'}</span>
                            <input id="amazon_template_upload" name="amazon_template_upload" type="file" className="sr-only" accept=".xlsm" onChange={(e) => setAmazonTemplate(e.target.files[0])} />
                        </label>
                        {amazonTemplate && <p className="text-xs text-gray-400 mt-2">Arquivo: {amazonTemplate.name}</p>}
                     </div>
                </div>
            </div>
            
            <form onSubmit={handleFinalSubmit}>
                <div className="flex justify-between items-center mt-12 mb-2">
                    <h1 className="text-3xl font-bold uppercase text-yellow-400">2. Valide ou Edite os dados</h1>
                    <button type="button" onClick={() => setProducts(prev => [...prev, createNewProduct({}, prev.length)])} className="flex items-center gap-2 px-4 py-2 text-sm font-bold text-black bg-yellow-400 rounded-lg hover:bg-yellow-500"><Plus size={18} />Adicionar Produto</button>
                </div>

                {products.map((product, index) => (
                    <ProductForm
                        key={product.id}
                        product={product}
                        index={index}
                        removeProduct={(id) => setProducts(prev => prev.filter(p => p.id !== id))}
                        handleProductChange={handleProductChange}
                        addVariation={addVariation}
                        removeVariation={removeVariation}
                        handleVariationChange={handleVariationChange}
                        handleImageChange={handleImageChange}
                        addExtraImage={addExtraImage}
                        removeExtraImage={removeExtraImage}
                        handleExtraImageChange={handleExtraImageChange}
                    />
                ))}
                
                <div className="mt-8 text-right">
                    <h2 className="text-2xl font-bold uppercase text-yellow-400 mb-4 text-right">3. Gere sua planilha final</h2>
                    <button type="submit" className="px-8 py-3 text-lg font-bold text-black bg-yellow-400 rounded-lg hover:bg-yellow-500 disabled:bg-gray-500 disabled:cursor-not-allowed" disabled={isLoading || products.length === 0 || !amazonTemplate}>
                        {isLoading ? 'Processando...' : 'Gerar Planilha Preenchida'}
                    </button>
                </div>
            </form>
        </div>
    );
}

export default CriarListing;
