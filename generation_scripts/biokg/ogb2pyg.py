# %%

from ogb.linkproppred import PygLinkPropPredDataset
from torch_geometric.data import HeteroData
from torch_geometric.transforms import ToUndirected
import os, json, pickle
import torch
import tqdm
# %%
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(BASE)

# %%
dataset = PygLinkPropPredDataset(name = "ogbl-biokg", root = os.path.join(BASE,'datafiles/'))
split_edge = dataset.get_edge_split()
train_edge, valid_edge, test_edge = split_edge["train"], split_edge["valid"], split_edge["test"]
graph = dataset[0]

# %%
all_index = {}
gci0_dir = os.path.join(BASE, 'datasets/biokg/gci0')
for fname in os.listdir(gci0_dir):
    if fname.startswith('class_index'):
        domain = fname.split('_')[-1].split('.')[0]
        fpath = os.path.join(gci0_dir, fname)
        with open(fpath, 'r') as fi:
            all_index[domain] = {int(k): v for k,v in json.load(fi).items()}
print(all_index)

# %%
rel_map = {}
f = os.path.join(BASE, 'datafiles/ogbl_biokg/mapping/relidx2relname.csv')
with open(f, 'r') as relfile:
    next(relfile)  # skip header
    for line in relfile:
        idx, name = line.strip().split(',', 1)
        rel_map[int(idx)] = name
print(rel_map)

# %%

edge_index_dict = {}
for i in tqdm.tqdm(range(len(train_edge['head']))):
    dom, ran = train_edge['head_type'][i], train_edge['tail_type'][i]
    h, t = train_edge['head'][i].item(), train_edge['tail'][i].item()
    r = rel_map[train_edge['relation'][i].item()]
    key = (dom, r, ran)
    if key in edge_index_dict:
        edge_index_dict[key].append((h, t))
    else:
        edge_index_dict[key] = [(h, t)]
# %%
pyg_data = HeteroData()
for k,v in all_index.items():
    pyg_data[k].node_id = torch.arange(len(v), dtype=torch.long)
for k, v in edge_index_dict.items():
    pyg_data[k].edge_index = torch.tensor(v, dtype=torch.long).T
    
pyg_data = ToUndirected(merge=False)(pyg_data)

# %%
pyg_valid = pyg_data.clone()
pyg_test = pyg_data.clone()
for target_graph, data in zip([pyg_valid, pyg_test], [valid_edge, test_edge]):
    pos_dict = {}
    neg_dict = {}
    for i in tqdm.tqdm(range(len(data['head_type']))):
        dom, ran = data['head_type'][i], data['tail_type'][i]
        h, t = data['head'][i].item(), data['tail'][i].item()
        hn, tn = data['head_neg'][i].tolist(), data['tail_neg'][i].tolist()
        r = rel_map[data['relation'][i].item()]
        key = (dom, r, ran)
        if key in pos_dict:
            pos_dict[key].append((h, t))
            neg_dict[key].append((hn, tn))
        else:
            pos_dict[key] = [(h, t)]
            neg_dict[key] = [(hn, tn)]
    # break
    for k in pos_dict:
        nbr_ex = len(pos_dict[k])
        nbr_neg = len(neg_dict[k][0][0])
        pos_ex = torch.tensor(pos_dict[k], dtype=torch.long).T
        neg_ex = torch.tensor(neg_dict[k], dtype=torch.long).permute([1,0,2])
        # ex = torch.tensor(pos_dict[k] + neg_dict[k], dtype=torch.long).T
        labels = torch.tensor([1.] * nbr_ex + [0.] * nbr_ex * nbr_neg, dtype=torch.float)
        target_graph[k].edge_label_index = torch.cat((pos_ex, neg_ex.reshape((2,-1))), dim=1)
        target_graph[k].edge_label = labels

        target_graph[k].pos_edge_label_index = pos_ex
        target_graph[k].neg_edge_label_index = neg_ex


# %%
gci_dir = os.path.join(BASE, 'datasets/biokg/gci0')
gci0_data = {}
for f in os.listdir(gci_dir):
    if 'gci0' in f:
        domain = f.split('_')[1].split('.')[0]
        with open(os.path.join(gci_dir, f), 'r') as fi:
            hierarchy = json.load(fi)
        # print(hierarchy)
        hierarchy = torch.tensor(hierarchy)
        # print(hierarchy)
        # print(hierarchy.shape)
        gci0_data[domain] = hierarchy
        # break
    # print(f)
# %%
DISEASE_MAX = 10686 + 1
DRUG_MAX = 10532 + 1
FUNCTION_MAX = 45084 + 1
PROTEIN_MAX = 17498 + 1
SIDEEFFECT_MAX = 9968 + 1
node_max_ids = {}
node_max_ids['disease'] = DISEASE_MAX
node_max_ids['drug'] = DRUG_MAX
node_max_ids['function'] = FUNCTION_MAX
node_max_ids['protein'] = PROTEIN_MAX
node_max_ids['sideeffect'] = SIDEEFFECT_MAX
# %%
with open(os.path.join(BASE, 'datasets/biokg/graphs.pkl'), 'wb') as fo:
    pickle.dump({'train': pyg_data, 'valid': pyg_valid, 'gci0': gci0_data, 'max_id': node_max_ids}, fo)
# %%
with open(os.path.join(BASE, 'datasets/biokg/test_graph.pkl'), 'wb') as fo:
    pickle.dump(pyg_test, fo)
# %%
