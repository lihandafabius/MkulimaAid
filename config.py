# config.py
import os
import torch
from torchvision import models, transforms
from transformers import AutoImageProcessor, AutoModelForImageClassification

class Config:
    SECRET_KEY = "supersecretkey"
    UPLOAD_FOLDER = './static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'jfif'}

    # Model paths
    DISEASE_MODEL_PATH = "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"
    PEST_MODEL_PATH = os.path.join('model', 'resnet50_0.497.pkl')

    # Load disease model (Plant Disease Identification)
    disease_processor = AutoImageProcessor.from_pretrained(DISEASE_MODEL_PATH)
    disease_model = AutoModelForImageClassification.from_pretrained(DISEASE_MODEL_PATH)

    # Load pest model (Custom ResNet50 for pest recognition)
    CLASS_NAMES = {
        0: 'rice leaf roller',
        1: 'rice leaf caterpillar',
        2: 'paddy stem maggot',
        3: 'asiatic rice borer',
        4: 'yellow rice borer',
        5: 'rice gall midge',
        6: 'Rice Stemfly',
        7: 'brown plant hopper',
        8: 'white backed plant hopper',
        9: 'small brown plant hopper',
        10: 'rice water weevil',
        11: 'rice leafhopper',
        12: 'grain spreader thrips',
        13: 'rice shell pest',
        14: 'grub',
        15: 'mole cricket',
        16: 'wireworm',
        17: 'white margined moth',
        18: 'black cutworm',
        19: 'large cutworm',
        20: 'yellow cutworm',
        21: 'red spider',
        22: 'corn borer',
        23: 'army worm',
        24: 'aphids',
        25: 'Potosiabre vitarsis',
        26: 'peach borer',
        27: 'english grain aphid',
        28: 'green bug',
        29: 'bird cherry-oat aphid',
        30: 'wheat blossom midge',
        31: 'penthaleus major',
        32: 'longlegged spider mite',
        33: 'wheat phloeothrips',
        34: 'wheat sawfly',
        35: 'cerodonta denticornis',
        36: 'beet fly',
        37: 'flea beetle',
        38: 'cabbage army worm',
        39: 'beet army worm',
        40: 'beet spot flies',
        41: 'meadow moth',
        42: 'beet weevil',
        43: 'sericaorient alismots chulsky',
        44: 'alfalfa weevil',
        45: 'flax budworm',
        46: 'alfalfa plant bug',
        47: 'tarnished plant bug',
        48: 'Locustoidea',
        49: 'lytta polita',
        50: 'legume blister beetle',
        51: 'blister beetle',
        52: 'therioaphis maculata Buckton',
        53: 'odontothrips loti',
        54: 'Thrips',
        55: 'alfalfa seed chalcid',
        56: 'Pieris canidia',
        57: 'Apolygus lucorum',
        58: 'Limacodidae',
        59: 'Viteus vitifoliae',
        60: 'Colomerus vitis',
        61: 'Brevipoalpus lewisi McGregor',
        62: 'oides decempunctata',
        63: 'Polyphagotars onemus latus',
        64: 'Pseudococcus comstocki Kuwana',
        65: 'parathrene regalis',
        66: 'Ampelophaga',
        67: 'Lycorma delicatula',
        68: 'Xylotrechus',
        69: 'Cicadella viridis',
        70: 'Miridae',
        71: 'Trialeurodes vaporariorum',
        72: 'Erythroneura apicalis',
        73: 'Papilio xuthus',
        74: 'Panonchus citri McGregor',
        75: 'Phyllocoptes oleiverus ashmead',
        76: 'Icerya purchasi Maskell',
        77: 'Unaspis yanonensis',
        78: 'Ceroplastes rubens',
        79: 'Chrysomphalus aonidum',
        80: 'Parlatoria zizyphus Lucus',
        81: 'Nipaecoccus vastalor',
        82: 'Aleurocanthus spiniferus',
        83: 'Tetradacus c Bactrocera minax',
        84: 'Dacus dorsalis (Hendel)',
        85: 'Bactrocera tsuneonis',
        86: 'Prodenia litura',
        87: 'Adristyrannus',
        88: 'Phyllocnistis citrella Stainton',
        89: 'Toxoptera citricidus',
        90: 'Toxoptera aurantii',
        91: 'Aphis citricola Vander Goot',
        92: 'Scirtothrips dorsalis Hood',
        93: 'Dasineura sp',
        94: 'Lawana imitata Melichar',
        95: 'Salurnis marginella Guerr',
        96: 'Deporaus marginatus Pascoe',
        97: 'Chlumetia transversa',
        98: 'Mango flat beak leafhopper',
        99: 'Rhytidodera bowrinii white',
        100: 'Sternochetus frigidus',
        101: 'Cicadellidae'
    }

    # Define and load ResNet50 for pest recognition
    pest_model = models.resnet50(pretrained=False)
    num_ftrs = pest_model.fc.in_features
    pest_model.fc = torch.nn.Linear(num_ftrs, len(CLASS_NAMES))
    pest_model.load_state_dict(torch.load(PEST_MODEL_PATH, map_location=torch.device('cpu')))
    pest_model.eval()

    # Define image transformations for pest recognition
    pest_transform = transforms.Compose([
        transforms.Resize((224, 224)),  # ResNet50 input size
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
