"""
Vector Store Management Page

Multi-page Streamlit app for managing OpenAI vector stores.
"""

import streamlit as st
import pandas as pd
from utils.streamlit_styles import inject_custom_css
from utils.vector_store_manager import (
    list_vector_stores,
    create_vector_store,
    delete_vector_store,
    get_vector_store_details,
    list_vector_store_files,
    remove_file_from_vector_store
)
from exceptions import VectorStoreError
from utils.logging_config import get_logger

# Initialize logging
logger = get_logger(__name__)

# Page config
st.set_page_config(
    page_title="Vector Stores • Triadic",
    page_icon=":material/storage:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject CSS
inject_custom_css()

# Page header
st.title(":material/storage: Vector Stores")
st.caption("Manage OpenAI vector stores for RAG")

st.divider()

# Main content
try:
    # List all vector stores
    with st.spinner("Loading vector stores..."):
        all_stores = list_vector_stores(limit=50)
    
    # Filter to show only stores that begin with "triadic"
    all_stores = [
        store for store in all_stores 
        if store.get("name") and store.get("name", "").lower().startswith("triadic")
    ]
    
    # Identify empty stores (zero files)
    empty_stores = []
    for store in all_stores:
        file_counts = store.get("file_counts", {})
        total_files = file_counts.get("in_progress", 0) + file_counts.get("completed", 0) + file_counts.get("failed", 0) + file_counts.get("cancelled", 0)
        if total_files == 0:
            empty_stores.append(store)
    
    # Cleanup section for empty stores
    if empty_stores:
        with st.expander(f":material/cleaning_services: Cleanup ({len(empty_stores)} empty stores)", expanded=False):
            st.caption(f"Found {len(empty_stores)} vector stores with zero files")
            
            # Show list of empty stores
            if len(empty_stores) <= 5:
                for store in empty_stores:
                    st.caption(f"• {store.get('name', 'Unnamed')} ({store.get('status', 'unknown')})")
            else:
                st.caption(f"• {len(empty_stores)} empty stores (too many to list)")
            
            # Purge button with confirmation
            purge_col1, purge_col2 = st.columns([1, 1])
            with purge_col1:
                if st.button(
                    f"Purge All Empty Stores ({len(empty_stores)})",
                    icon=":material/delete_sweep:",
                    use_container_width=True,
                    type="secondary"
                ):
                    st.session_state["_confirm_purge_empty"] = True
                    st.rerun()
            
            # Confirmation dialog
            if st.session_state.get("_confirm_purge_empty", False):
                st.warning(f":material/warning: Delete {len(empty_stores)} empty vector stores? This cannot be undone!")
                confirm_col1, confirm_col2 = st.columns(2)
                with confirm_col1:
                    if st.button("Yes, Purge All", key="confirm_purge", type="primary", use_container_width=True):
                        deleted_count = 0
                        failed_count = 0
                        current_vs_id = st.session_state.get("vector_store_id")
                        
                        for store in empty_stores:
                            try:
                                delete_vector_store(store["id"])
                                deleted_count += 1
                                # If current store is being deleted, detach it
                                if current_vs_id == store["id"]:
                                    st.session_state.vector_store_id = None
                                    st.session_state.uploaded_file_index = {}
                            except Exception as e:
                                logger.error(f"Failed to delete {store.get('name', 'Unnamed')}: {e}")
                                failed_count += 1
                        
                        if deleted_count > 0:
                            st.toast(f"Purged {deleted_count} empty stores", icon=":material/check_circle:")
                        if failed_count > 0:
                            st.error(f"Failed to delete {failed_count} stores")
                        
                        st.session_state["_confirm_purge_empty"] = False
                        st.rerun()
                
                with confirm_col2:
                    if st.button("Cancel", key="cancel_purge", use_container_width=True):
                        st.session_state["_confirm_purge_empty"] = False
                        st.rerun()
        
        st.divider()
    
    # Current vector store section (if any)
    current_vs_id = st.session_state.get("vector_store_id")
    if current_vs_id:
        try:
            current_details = get_vector_store_details(current_vs_id)
            file_counts = current_details.get("file_counts", {})
            total_files = file_counts.get("in_progress", 0) + file_counts.get("completed", 0)
            
            with st.container():
                st.markdown("### :material/check_circle: Active Vector Store")
                active_col1, active_col2 = st.columns([4, 1])
                with active_col1:
                    st.markdown(f"**{current_details.get('name', 'Unnamed')}**")
                    st.caption(f":material/description: {total_files} files • :material/info: {current_details.get('status', 'unknown')}")
                with active_col2:
                    if st.button("Detach", icon=":material/link_off:", key="detach_vs", use_container_width=True, type="secondary"):
                        st.session_state.vector_store_id = None
                        st.session_state.uploaded_file_index = {}
                        st.toast("Vector store detached!", icon=":material/link_off:")
                        st.rerun()
                st.divider()
        except Exception as e:
            logger.warning(f"Could not get details for current vector store: {e}")
            st.warning(f":material/warning: Current vector store may be invalid")
            if st.button("Detach Invalid Store", icon=":material/link_off:", key="detach_invalid_vs", use_container_width=True):
                st.session_state.vector_store_id = None
                st.session_state.uploaded_file_index = {}
                st.rerun()
            st.divider()
    
    # List all vector stores in datagrid
    if not all_stores:
        st.info(":material/info: No vector stores found. Create one to get started!", icon=":material/info:")
    else:
        st.markdown("### :material/storage: All Vector Stores")
        
        # Prepare DataFrame
        df_data = []
        for store in all_stores:
            vs_id = store["id"]
            vs_name = store.get("name", "Unnamed")
            file_counts = store.get("file_counts", {})
            total_files = file_counts.get("in_progress", 0) + file_counts.get("completed", 0)
            status = store.get("status", "unknown")
            is_current = (current_vs_id == vs_id)
            
            df_data.append({
                "Active": "✓" if is_current else "",
                "Name": vs_name,
                "Files": total_files,
                "Status": status,
                "ID": vs_id[:30] + "...",
                "_vs_id": vs_id  # Hidden column for actions
            })
        
        df = pd.DataFrame(df_data)
        
        # Configure column display
        column_config = {
            "Active": st.column_config.TextColumn(
                "Active",
                width="small",
                help="Active vector store indicator"
            ),
            "Name": st.column_config.TextColumn(
                "Name",
                width="medium",
                help="Vector store name"
            ),
            "Files": st.column_config.NumberColumn(
                "Files",
                width="small",
                help="Number of files",
                format="%d"
            ),
            "Status": st.column_config.TextColumn(
                "Status",
                width="small",
                help="Vector store status"
            ),
            "ID": st.column_config.TextColumn(
                "ID",
                width="large",
                help="Vector store ID (truncated)"
            ),
            "_vs_id": st.column_config.TextColumn(
                "_vs_id",
                width="small",
                disabled=True
            )
        }
        
        # Display dataframe with multi-row selection
        selected_rows = st.dataframe(
            df,
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row"
        )
        
        # Actions for selected stores
        if selected_rows.selection.rows:
            num_selected = len(selected_rows.selection.rows)
            selected_indices = selected_rows.selection.rows
            selected_stores = [all_stores[idx] for idx in selected_indices]
            
            st.divider()
            
            if num_selected == 1:
                # Single store selected - show detailed actions
                selected_store = selected_stores[0]
                vs_id = selected_store["id"]
                vs_name = selected_store.get("name", "Unnamed")
                file_counts = selected_store.get("file_counts", {})
                total_files = file_counts.get("in_progress", 0) + file_counts.get("completed", 0)
                is_current = (current_vs_id == vs_id)
                
                st.markdown(f"#### Actions: {vs_name}")
                
                # Action buttons
                action_col1, action_col2, action_col3, action_col4 = st.columns(4)
                
                with action_col1:
                    if not is_current:
                        if st.button("Attach", key=f"attach_{vs_id}", icon=":material/link:", use_container_width=True, type="primary"):
                            st.session_state.vector_store_id = vs_id
                            st.session_state.uploaded_file_index = {}
                            st.session_state.last_processed_files = set()
                            st.toast(f"Attached: {vs_name}", icon=":material/link:")
                            st.rerun()
                    else:
                        st.success("Active", icon=":material/check_circle:")
                
                with action_col2:
                    cache_key = f"_files_cache_{vs_id}"
                    if total_files > 0:
                        if cache_key not in st.session_state:
                            if st.button("Load Files", key=f"load_files_{vs_id}", icon=":material/folder:", use_container_width=True):
                                with st.spinner("Loading files..."):
                                    try:
                                        st.session_state[cache_key] = list_vector_store_files(vs_id, limit=100)
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Failed: {e}")
                                        st.session_state[cache_key] = []
                
                with action_col3:
                    if st.button("View Details", key=f"details_{vs_id}", icon=":material/info:", use_container_width=True):
                        st.session_state[f"_show_details_{vs_id}"] = True
                        st.rerun()
                
                with action_col4:
                    if st.button("Delete", key=f"delete_{vs_id}", icon=":material/delete:", use_container_width=True, type="secondary"):
                        st.session_state[f"_confirm_delete_{vs_id}"] = True
                        st.rerun()
            else:
                # Multiple stores selected - show bulk actions
                st.markdown(f"#### Bulk Actions: {num_selected} stores selected")
                
                # Show selected store names
                selected_names = [store.get("name", "Unnamed") for store in selected_stores]
                st.caption(f"Selected: {', '.join(selected_names[:5])}{'...' if len(selected_names) > 5 else ''}")
                
                bulk_col1, bulk_col2 = st.columns(2)
                
                with bulk_col1:
                    if st.button("Delete Selected", icon=":material/delete:", use_container_width=True, type="secondary"):
                        st.session_state["_bulk_delete_stores"] = [store["id"] for store in selected_stores]
                        st.session_state["_confirm_bulk_delete"] = True
                        st.rerun()
                
                with bulk_col2:
                    # Count empty stores
                    empty_count = sum(
                        1 for store in selected_stores
                        if (store.get("file_counts", {}).get("in_progress", 0) + 
                            store.get("file_counts", {}).get("completed", 0) +
                            store.get("file_counts", {}).get("failed", 0) +
                            store.get("file_counts", {}).get("cancelled", 0)) == 0
                    )
                    if empty_count > 0:
                        st.caption(f":material/info: {empty_count} of {num_selected} selected stores are empty")
            
            # Bulk delete confirmation
            if st.session_state.get("_confirm_bulk_delete", False):
                bulk_delete_ids = st.session_state.get("_bulk_delete_stores", [])
                if bulk_delete_ids:
                    st.warning(f":material/warning: Delete {len(bulk_delete_ids)} selected vector stores? This cannot be undone!")
                    confirm_col1, confirm_col2 = st.columns(2)
                    with confirm_col1:
                        if st.button("Yes, Delete All", key="confirm_bulk_delete", type="primary", use_container_width=True):
                            # Initialize progress tracking
                            st.session_state["_bulk_delete_in_progress"] = True
                            st.session_state["_bulk_delete_progress"] = 0
                            st.session_state["_bulk_delete_total"] = len(bulk_delete_ids)
                            st.session_state["_bulk_delete_results"] = {"deleted": [], "failed": []}
                            st.rerun()
                    
                    with confirm_col2:
                        if st.button("Cancel", key="cancel_bulk_delete", use_container_width=True):
                            st.session_state["_confirm_bulk_delete"] = False
                            st.session_state["_bulk_delete_stores"] = []
                            st.rerun()
            
            # Show progress during bulk deletion
            if st.session_state.get("_bulk_delete_in_progress", False):
                bulk_delete_ids = st.session_state.get("_bulk_delete_stores", [])
                total = st.session_state.get("_bulk_delete_total", len(bulk_delete_ids))
                current = st.session_state.get("_bulk_delete_progress", 0)
                results = st.session_state.get("_bulk_delete_results", {"deleted": [], "failed": []})
                
                # Progress bar
                progress = current / total if total > 0 else 0
                st.progress(progress, text=f"Deleting stores... {current}/{total}")
                
                # Status message
                if current < total:
                    current_store_id = bulk_delete_ids[current]
                    current_store = next((s for s in all_stores if s["id"] == current_store_id), None)
                    store_name = current_store.get("name", "Unknown") if current_store else "Unknown"
                    st.caption(f":material/hourglass_empty: Deleting: **{store_name}** ({current + 1}/{total})")
                    
                    # Perform deletion
                    try:
                        delete_vector_store(current_store_id)
                        if current_vs_id == current_store_id:
                            st.session_state.vector_store_id = None
                            st.session_state.uploaded_file_index = {}
                        results["deleted"].append(current_store_id)
                    except Exception as e:
                        logger.error(f"Failed to delete {current_store_id}: {e}")
                        results["failed"].append(current_store_id)
                    
                    # Update progress
                    st.session_state["_bulk_delete_progress"] = current + 1
                    st.session_state["_bulk_delete_results"] = results
                    
                    # Small delay for visual feedback
                    import time
                    time.sleep(0.3)
                    st.rerun()
                else:
                    # Deletion complete
                    deleted_count = len(results["deleted"])
                    failed_count = len(results["failed"])
                    
                    st.success(f":material/check_circle: Deletion complete!")
                    
                    if deleted_count > 0:
                        st.toast(f"Deleted {deleted_count} stores", icon=":material/delete:")
                    if failed_count > 0:
                        st.error(f"Failed to delete {failed_count} stores")
                    
                    # Show summary
                    summary_col1, summary_col2 = st.columns(2)
                    with summary_col1:
                        st.metric("Deleted", deleted_count, delta=None)
                    with summary_col2:
                        if failed_count > 0:
                            st.metric("Failed", failed_count, delta=None, delta_color="inverse")
                    
                    # Reset state
                    st.session_state["_bulk_delete_in_progress"] = False
                    st.session_state["_confirm_bulk_delete"] = False
                    st.session_state["_bulk_delete_stores"] = []
                    st.session_state["_bulk_delete_progress"] = 0
                    st.session_state["_bulk_delete_total"] = 0
                    st.session_state["_bulk_delete_results"] = {"deleted": [], "failed": []}
                    
                    # Auto-refresh after a moment
                    import time
                    time.sleep(1.5)
                    st.rerun()
        
        # Show details, files, and delete confirmation in expanders
        for store in all_stores:
            vs_id = store["id"]
            vs_name = store.get("name", "Unnamed")
            
            if st.session_state.get(f"_show_details_{vs_id}", False):
                with st.expander(f"Details: {vs_name}", expanded=True):
                    try:
                        details = get_vector_store_details(vs_id)
                        st.json(details)
                    except Exception as e:
                        st.error(f"Failed: {e}")
                    if st.button("Close", key=f"close_details_{vs_id}"):
                        st.session_state[f"_show_details_{vs_id}"] = False
                        st.rerun()
            
            # Show files if loaded
            cache_key = f"_files_cache_{vs_id}"
            if cache_key in st.session_state:
                with st.expander(f"Files: {vs_name}", expanded=False):
                    files = st.session_state.get(cache_key, [])
                    if files:
                        if len(files) >= 100:
                            st.warning(f":material/info: Showing first 100 files")
                        
                        if st.button("Refresh", key=f"refresh_files_{vs_id}", icon=":material/refresh:", use_container_width=True):
                            with st.spinner("Refreshing..."):
                                try:
                                    st.session_state[cache_key] = list_vector_store_files(vs_id, limit=100)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed: {e}")
                        
                        st.divider()
                        
                        # Display files in a dataframe too
                        files_df = pd.DataFrame(files)
                        if not files_df.empty:
                            files_df_display = files_df[["name", "status", "bytes"]].copy()
                            files_df_display["bytes"] = files_df_display["bytes"].apply(lambda x: f"{x:,}")
                            files_df_display.columns = ["File Name", "Status", "Size (bytes)"]
                            
                            st.dataframe(
                                files_df_display,
                                use_container_width=True,
                                hide_index=True
                            )
                            
                            # Remove file buttons
                            for file_info in files:
                                file_id = file_info.get("id", "")
                                file_name = file_info.get("name", "unknown")
                                if st.button(f"Remove {file_name}", key=f"remove_{file_id}", type="secondary"):
                                    try:
                                        remove_file_from_vector_store(vs_id, file_id)
                                        if cache_key in st.session_state:
                                            del st.session_state[cache_key]
                                        st.toast(f"Removed {file_name}", icon=":material/delete:")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Failed: {e}")
                    else:
                        st.caption("No files")
            
            # Confirm delete
            if st.session_state.get(f"_confirm_delete_{vs_id}", False):
                with st.expander(f"Confirm Delete: {vs_name}", expanded=True):
                    st.warning(f":material/warning: Delete '{vs_name}'? This cannot be undone!")
                    confirm_col1, confirm_col2 = st.columns(2)
                    with confirm_col1:
                        if st.button("Yes, Delete", key=f"confirm_delete_{vs_id}", type="primary", use_container_width=True):
                            try:
                                delete_vector_store(vs_id)
                                if current_vs_id == vs_id:
                                    st.session_state.vector_store_id = None
                                    st.session_state.uploaded_file_index = {}
                                st.session_state[f"_confirm_delete_{vs_id}"] = False
                                st.toast(f"Deleted: {vs_name}", icon=":material/delete:")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed: {e}")
                    with confirm_col2:
                        if st.button("Cancel", key=f"cancel_delete_{vs_id}", use_container_width=True):
                            st.session_state[f"_confirm_delete_{vs_id}"] = False
                            st.rerun()
    
    st.divider()
    
    # Create new vector store
    st.markdown("### :material/add: Create New Vector Store")
    new_store_name = st.text_input(
        "Vector Store Name",
        value="triadic-store",
        help="Name for the new vector store",
        key="new_vector_store_name"
    )
    
    create_col1, create_col2 = st.columns([1, 1])
    with create_col1:
        if st.button("Create", icon=":material/add:", use_container_width=True, type="primary"):
            if new_store_name:
                try:
                    new_vs_id = create_vector_store(new_store_name)
                    st.session_state.vector_store_id = new_vs_id
                    st.session_state.uploaded_file_index = {}
                    st.session_state.last_processed_files = set()
                    st.toast(f"Created and attached: {new_store_name}", icon=":material/check_circle:")
                    st.rerun()
                except VectorStoreError as e:
                    st.error(f"Failed to create: {e}")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")
                    logger.error(f"Unexpected error creating vector store: {e}", exc_info=True)
            else:
                st.warning("Please enter a name for the vector store")

except VectorStoreError as e:
    st.error(f"Vector store error: {e}", icon=":material/error:")
    logger.error(f"Vector store management error: {e}", exc_info=True)
except Exception as e:
    st.error(f"Unexpected error: {e}", icon=":material/error:")
    logger.error(f"Unexpected error in vector store management: {e}", exc_info=True)

